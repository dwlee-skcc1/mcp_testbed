from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import json
import os
import uuid
import redis
from celery import Celery
import logging
import importlib
import pkgutil
import inspect
from pathlib import Path
# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis 설정
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
TOOL_PORT = int(os.getenv("TOOL_PORT", "8001"))

# Redis 클라이언트 초기화
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Celery 설정
celery_app = Celery('mcp_tasks', 
                    broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
                    backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')

app = FastAPI()
        
# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
        
# 도구 정보 클래스
class ToolInfo(BaseModel):
    name: str
    description: str
    version: Optional[str] = "1.0"
    args_schema: Optional[Dict] = {}
    queue: Optional[str] = "default"

# 도구 실행 요청 클래스
class ToolRequest(BaseModel):
    tool_name: str
    args: Dict[str, Any] = {}
    callback_url: Optional[str] = None

# 도구 목록 (메모리에 캐시)
tools_cache = {}

# 도구 등록 함수
def register_tool(tool_info: Dict):
    """도구 정보를 Redis에 등록"""
    tool_name = tool_info.get("name")
    if not tool_name:
        logger.error("Tool name is required")
        return False
    
    redis_key = f"tool:{tool_name}"
    try:
        redis_client.set(redis_key, json.dumps(tool_info))
        # 메모리 캐시도 업데이트
        tools_cache[tool_name] = tool_info
        logger.info(f"Tool {tool_name} registered successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to register tool {tool_name}: {str(e)}")
        return False


# 도구 자동 발견 및 등록
@app.on_event("startup")
async def discover_and_register_tools():
    """서버 시작 시 모든 도구 자동 발견 및 등록"""
    # 1. 명시적으로 정의된 기본 도구 등록
    default_tools = [
        # ... 기존 default_tools 리스트 ...
    ]
    
    for tool in default_tools:
        register_tool(tool)
    
    # 2. tools 디렉토리에서 모든 도구 모듈 자동 발견
    try:
        # 도구 디렉토리 경로
        tools_dir = Path(__file__).parent / "tools"
        logger.info(f"Discovering tools in: {tools_dir}")
        
        # 도구 디렉토리가 존재하는지 확인
        if not tools_dir.exists() or not tools_dir.is_dir():
            logger.warning(f"Tools directory not found: {tools_dir}")
            return
        
        # tools 패키지 임포트
        import mcp_server.tools
        
        # 모든 모듈 탐색
        for _, module_name, is_pkg in pkgutil.iter_modules([str(tools_dir)]):
            if is_pkg or not module_name.endswith('_tool'):
                continue  # _tool로 끝나는 파일만 처리
                
            try:
                # 모듈 동적 로드
                module_path = f"mcp_server.tools.{module_name}"
                module = importlib.import_module(module_path)
                logger.info(f"Found tool module: {module_path}")
                
                # 방법 1: REGISTERED_TOOLS 리스트 확인
                if hasattr(module, "REGISTERED_TOOLS"):
                    for tool_info in getattr(module, "REGISTERED_TOOLS", []):
                        tool_name = tool_info.get("name", "unknown")
                        logger.info(f"Registering tool: {tool_name} from {module_path}")
                        register_tool(tool_info)
                
                # 방법 2: 데코레이터로 등록된 함수 찾기
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if hasattr(func, "_tool_info"):
                        tool_info = getattr(func, "_tool_info")
                        logger.info(f"Registering decorated tool: {tool_info['name']} from {module_path}")
                        register_tool(tool_info)
                        
            except Exception as e:
                logger.error(f"Error loading tool module {module_name}: {str(e)}", exc_info=True)
    
    except Exception as e:
        logger.error(f"Error discovering tools: {str(e)}", exc_info=True)
        
    # 등록된 모든 도구 로깅
    logger.info(f"Total registered tools: {len(tools_cache)}")
    for tool_name in tools_cache:
        logger.info(f"  - {tool_name}")

# SSE 엔드포인트: 도구 목록 제공
@app.get("/sse/tools")
async def get_tools():
    """등록된 모든 도구 목록 반환"""
    try:
        # 캐시된 도구 정보가 있으면 사용
        if tools_cache:
            return list(tools_cache.values())
        
        # 캐시가 없으면 Redis에서 로드
        tools = []
        for key in redis_client.keys("tool:*"):
            tool_data = redis_client.get(key)
            if tool_data:
                tool_info = json.loads(tool_data)
                tools.append(tool_info)
                # 캐시 업데이트
                tools_cache[tool_info["name"]] = tool_info
        
        return tools
    except Exception as e:
        logger.error(f"Error getting tools: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

# SSE 엔드포인트: 도구 실행
@app.post("/sse/run")
async def run_tool(request: ToolRequest, background_tasks: BackgroundTasks):
    """도구 비동기 실행 요청"""
    tool_name = request.tool_name
    
    # Redis에서 도구 정보 확인(redis가 도구의 메타데이터 중앙 저장소 -> 해당 도구가 유효한지, 어떤 워커가 담당해야하고, 어떤 큐에서 처리해야하는지, 실행상태와 결과를 저장하고 추적하기 위해)
    tool_key = f"tool:{tool_name}"
    tool_data = redis_client.get(tool_key)
    
    if not tool_data:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
    
    tool_info = json.loads(tool_data)
    queue_name = tool_info.get("queue", "default")
    
    # 실행 ID 생성
    execution_id = str(uuid.uuid4())
    
    # 작업 상태 초기화
    redis_client.set(f"execution:{execution_id}", json.dumps({
        "status": "pending",
        "tool": tool_name,
        "args": request.args,
        "result": None
    }))
    
    # Celery 작업 비동기 실행
    background_tasks.add_task(
        dispatch_tool_task,
        tool_name=tool_name,
        args=request.args,
        execution_id=execution_id,
        queue=queue_name,
        callback_url=request.callback_url
    )
    
    return {"execution_id": execution_id, "status": "pending"}

async def dispatch_tool_task(tool_name: str, args: Dict, execution_id: str, queue: str, callback_url: Optional[str] = None):
    """Celery 작업 디스패치""" #프로그램이 tool을 호출할 것인가를 결정하여 그것을 실행하는 과정
    #사용자 쿼리 > llm이 도구 호출 필요하다고 결정 > fastapi 서버가 mcp 서버의 /sse/run 엔드포인트로 전송 > mcp 서버가 dispatch_tool_task 호출
    try:
        # 도구 실행 Celery 태스크 호출
        logger.info(f"Dispatching task for tool {tool_name} with args {args}")
        task = celery_app.send_task(
            "celery_workers.tasks.execute_tool",
            args=[tool_name, args, execution_id],
            kwargs={"callback_url": callback_url},
            queue=queue
        )
        
        # 작업 ID 저장
        redis_client.set(f"execution_task:{execution_id}", task.id)
        logger.info(f"Task dispatched with ID {task.id} for execution {execution_id}")
        
    except Exception as e:
        logger.error(f"Error dispatching task: {str(e)}")
        # 오류 상태 업데이트
        redis_client.set(f"execution:{execution_id}", json.dumps({
            "status": "error",
            "tool": tool_name,
            "args": args,
            "result": {"error": str(e)}
        }))

# 도구 실행 상태 확인
@app.get("/sse/status/{execution_id}")
async def get_execution_status(execution_id: str):
    """도구 실행 상태 확인"""
    execution_data = redis_client.get(f"execution:{execution_id}")
    
    if not execution_data:
        raise HTTPException(status_code=404, detail=f"Execution {execution_id} not found")
    
    return json.loads(execution_data)

# 새 도구 등록 엔드포인트
@app.post("/sse/register")
async def register_new_tool(tool: ToolInfo):
    """새 도구 등록"""
    tool_dict = tool.dict()
    success = register_tool(tool_dict)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to register tool")
    
    return {"status": "success", "message": f"Tool {tool.name} registered successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=TOOL_PORT)