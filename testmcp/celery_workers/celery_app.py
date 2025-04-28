from celery import Celery
import os
import importlib
import json
import redis
import logging
import requests
from typing import Dict, Any, Optional

from celery_workers.tools import math_tool
from celery_workers.tasks.math_tasks import divide

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 환경 변수
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MCP_SERVER = os.getenv("MCP_SERVER_HOST", "mcp_server")
TOOL_PORT = int(os.getenv("TOOL_PORT", "8001"))

# Redis 클라이언트
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

# Celery 앱 초기화
app = Celery('celery_workers',
             broker=f'redis://{REDIS_HOST}:{REDIS_PORT}/0',
             backend=f'redis://{REDIS_HOST}:{REDIS_PORT}/0')

# Celery 설정
app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1,  # 1개 작업 후 워커 프로세스 재시작
    task_routes={
        'celery_workers.tasks.execute_tool': {'queue': 'default'},
    }
)

# 도구 모듈 캐시
tool_modules = {}

# 도구 실행기 태스크 - 여기에 mcp client가 들어가고, llm 들어가서
@app.task(name="celery_workers.tasks.execute_tool", bind=True)
def execute_tool(self, tool_name: str, args: Dict[str, Any], execution_id: str, callback_url: Optional[str] = None):
    """
    동적으로 도구를 로드하고 실행하는 태스크
    """
    logger.info(f"Executing tool {tool_name} with args {args}")
    
    try:
        # 도구 정보 가져오기
        tool_info = get_tool_info(tool_name)
        if not tool_info:
            raise ValueError(f"Tool {tool_name} not found")
        
        # 도구 모듈 로드 (캐시 확인)
        if tool_name not in tool_modules:
            tool_modules[tool_name] = load_tool_module(tool_name)
        
        tool_module = tool_modules[tool_name]
        if not tool_module:
            raise ImportError(f"Failed to load module for tool {tool_name}")
        
    
        logger.info("tool_module",tool_module)
        # 도구 실행
        
        logger.info("tool_module.__call__",tool_module.__call__)
        
        
        result = tool_module(**args)
        
        # 결과 저장
        update_execution_status(execution_id, "completed", result)
        
        # 콜백 URL이 있으면 결과 전송
        if callback_url:
            send_callback(callback_url, {
                "execution_id": execution_id,
                "status": "completed",
                "result": result
            })
        
        return {"status": "success", "result": result}
    
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}", exc_info=True)
        # 실행 상태 업데이트
        update_execution_status(execution_id, "error", {"error": str(e)})
        
        # 콜백 URL이 있으면 오류 전송
        if callback_url:
            send_callback(callback_url, {
                "execution_id": execution_id,
                "status": "error",
                "error": str(e)
            })
        
        # 오류를 반환해도 태스크는 성공으로 처리 (재시도 방지)
        return {"status": "error", "error": str(e)}

def get_tool_info(tool_name: str) -> Dict:
    """
    Redis에서 도구 정보 가져오기
    """
    try:
        tool_data = redis_client.get(f"tool:{tool_name}")
        logger.info("tool_data_1234",tool_data)
        if tool_data:
            return json.loads(tool_data)
        
        # Redis에 없으면 MCP 서버에서 도구 정보 가져오기
        response = requests.get(f"http://{MCP_SERVER}:{TOOL_PORT}/sse/tools")
        
        logger.info("response_1234",response)
        logger.info("tools_1234",f"http://{MCP_SERVER}:{TOOL_PORT}/sse/tools")
        if response.status_code == 200:
            tools = response.json()
            logger.info("tools_1234",tools)
            
            for tool in tools:
                if tool.get("name") == tool_name:
                    # Redis에 캐싱
                    redis_client.set(f"tool:{tool_name}", json.dumps(tool))
                    return tool
        
        return None
    except Exception as e:
        logger.error(f"Error getting tool info: {str(e)}")
        return None

def load_tool_module(tool_name: str):
    """도구 모듈 동적 로드 - 다양한 위치 탐색"""
    tool_dict = {
        "divide": math_tool.divide,
    }
    
    return tool_dict.get(tool_name)
    


def update_execution_status(execution_id: str, status: str, result: Any):
    """
    도구 실행 상태 업데이트
    """
    try:
        # 현재 실행 데이터 가져오기
        execution_data = redis_client.get(f"execution:{execution_id}")
        if execution_data:
            data = json.loads(execution_data)
            data["status"] = status
            data["result"] = result
            
            # 업데이트된 데이터 저장
            redis_client.set(f"execution:{execution_id}", json.dumps(data))
            logger.info(f"Updated execution {execution_id} status to {status}")
        else:
            logger.warning(f"Execution {execution_id} not found in Redis")
    except Exception as e:
        logger.error(f"Error updating execution status: {str(e)}")

def send_callback(callback_url: str, data: Dict):
    """
    콜백 URL로 결과 전송
    """
    try:
        response = requests.post(
            callback_url,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        logger.info(f"Callback sent to {callback_url}, status: {response.status_code}")
    except Exception as e:
        logger.error(f"Error sending callback: {str(e)}")
        

