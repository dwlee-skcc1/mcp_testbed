from fastapi import APIRouter, HTTPException
import os
from dotenv import load_dotenv
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient


from utils.mcp_response import MessageHandler
from services.sample_service import SampleService
from services.agent.sample_agent import SampleAgent, SampleConnectAgent
from services.schemas.chat.request import OpenAIRequest
from services.schemas.chat.response import SampleResponse
from core.llm import get_model

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent.parent / "tool" 



router = APIRouter()


@router.post("/connect_sse")
async def test_connect():
    """
    SSE test connection
    """
    sample_service = SampleService()
    graph = SampleConnectAgent().get_graph()
    return await sample_service.tool_test(tools=["sse"], graph=graph)


@router.post("/chat_sse", response_model=SampleResponse)
async def chat_sse_test(request:OpenAIRequest):
    """
    SSE test connection to "test" tool
    """
    sample_service = SampleService()
    graph = await SampleAgent(llm=get_model()).get_graph()
    return await sample_service.chat_test_completion(tools=["sse"], request=request, graph=graph)


### 아래 api는 모두 테스트 중

@router.post("/connect_stdio")
async def connect_stdio():
    """
    STDIO test connection
    """
    sample_service = SampleService()
    graph = SampleConnectAgent().get_graph()
    return await sample_service.tool_test(tools=["stdio"], graph=graph)



@router.get("/chat_stdio")
async def chat_stdio(request:OpenAIRequest):
    """
    STDIO test connection to "test" tool
    """
    sample_service = SampleService()
    graph = await SampleAgent(llm=get_model()).get_graph()
    return await sample_service.chat_test_completion(tools=["stdio"], request=request, graph=graph)

