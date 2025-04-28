from fastapi import APIRouter, HTTPException, Query
import os
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json

from fastapi_server.services.sample_service import SampleService
from fastapi_server.services.schemas.chat.request import OpenAIRequest
from fastapi_server.services.schemas.chat.response import SampleResponse
from fastapi_server.services.agent.sample_agent import SampleConnectAgent, SampleAgent, ToolIntegrationAgent
from fastapi_server.services.agent.tool_callback_manager import callback_manager

# 환경 변수 로드
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

# 라우터 생성
router = APIRouter()

# 서비스 인스턴스
sample_service = SampleService()

@router.post("/connect_sse", response_model=SampleResponse)
async def test_connect():
    """SSE 도구 연결 테스트 (예제)"""
    try:
        return await sample_service.tool_test(tools=["sse"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Connection test failed: {str(e)}")

@router.post("/chat_sse", response_model=SampleResponse)
async def chat_sse_test(request: OpenAIRequest):
    """SSE 도구를 사용한 LLM 채팅 테스트 (예제)"""
    try:
        return await sample_service.chat_test_completion(tools=["sse"], request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@router.post("/connect_stdio")
async def connect_stdio():
    """STDIO 도구 연결 테스트 (예제)"""
    try:
        return await sample_service.tool_test(tools=["stdio"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STDIO connection failed: {str(e)}")

@router.post("/chat_stdio", response_model=SampleResponse)
async def chat_stdio(request: OpenAIRequest):
    """STDIO 도구를 사용한 LLM 채팅 테스트 (예제)"""
    try:
        return await sample_service.chat_test_completion(tools=["stdio"], request=request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"STDIO chat failed: {str(e)}")

@router.post("/chat_math", response_model=SampleResponse)
async def chat_math(request: OpenAIRequest):
    try:
        print(f"=== 수학 도구 채팅 시작 ===")
        result = await sample_service.chat_test_completion(tools=["math"], request=request)
        print(f"=== 도구 사용 결과: {result} ===")
        return result
    except Exception as e:
        print(f"오류 발생: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Math chat failed: {str(e)}")

class ToolIntegrationRequest(BaseModel):
    user_query: str
    tool: List[str] = ["math_queue"]  # 기본값을 math_queue로 변경
    messages: Optional[List[Dict[str, Any]]] = None
    
# 통합 엔드포인트 (일반화된 도구 사용 채팅)
@router.post("/chat", response_model=SampleResponse)
async def chat_with_tools(request: ToolIntegrationRequest):
    """도구를 활용한 LLM 채팅"""
    try:
        print("====== 요청 시작 ======")
        print(f"요청 데이터: {request.dict()}")
        
        agent = ToolIntegrationAgent()
        state = request.dict()
        
        # 코드 실행 그래프 가져오기
        print("그래프 가져오기...")
        graph = await agent.get_graph()
        
        # 그래프 실행
        print("그래프 실행...")
        result = await graph.ainvoke(state)
        print(f"실행 결과: {result}")
        
        answer = result.get("answer", "") if isinstance(result, dict) else str(result)
        print(f"최종 응답: {answer}")
        print("====== 요청 완료 ======")
        
        return {"answer": answer}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"====== 오류 발생 ======")
        print(error_trace)
        print("======================")
        raise HTTPException(status_code=500, detail=str(e))

# 도구 콜백 엔드포인트
class ToolCallbackRequest(BaseModel):
    """도구 실행 콜백 요청"""
    execution_id: str
    status: str
    result: Dict[str, Any] = {}
    error: Optional[str] = None

@router.post("/tool_callback")
async def tool_callback(request: ToolCallbackRequest):
    """도구 실행 결과 콜백 수신"""
    try:
        print("====== 콜백 수신 ======")
        print(f"콜백 데이터: {request.dict()}")
        
        # 콜백 데이터를 Redis에 저장
        callback_key = f"callback:{request.execution_id}"
        redis_host = os.getenv("REDIS_HOST", "redis")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        try:
            import redis
            redis_client = redis.Redis(host=redis_host, port=redis_port, db=0)
            redis_client.set(callback_key, json.dumps(request.dict()))
            print(f"콜백 데이터 저장: {callback_key}")
        except Exception as redis_err:
            print(f"Redis 저장 오류: {str(redis_err)}")
        
        # 콜백 매니저에 결과 설정
        callback_manager.set_result(request.execution_id, request.dict())
        print(f"콜백 매니저에 결과 설정: {request.execution_id}")
        
        print("====== 콜백 처리 완료 ======")
        return {"status": "success", "message": "Callback received"}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"====== 콜백 처리 오류 ======")
        print(error_trace)
        print("======================")
        return {"status": "error", "message": str(e)}