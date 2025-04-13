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


@router.post("/test_connect")
async def test_connect():
    """
    SSE test connection
    """
    graph = SampleConnectAgent().get_graph()
    response = await graph.ainvoke({})
    return response


@router.post("/chat_sse_test", response_model=SampleResponse)
async def chat_sse_test(request:OpenAIRequest):
    """
    SSE test connection to "test" tool
    """
    sample_service = SampleService()
    graph = await SampleAgent(llm=get_model()).get_graph()
    return await sample_service.chat_sse_test_completion(request, graph)


### 아래 api는 모두 테스트 중

@router.get("/connect_stdio")
async def connect_stdio():
    async with MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["%s/math.py"%tool_dir],
                "transport": "stdio",
            }
        }
    ) as client:
        print("here")
        await client.__aenter__()
        tools = client.get_tools()

    return {"response":tools}



@router.get("/chat_stdio")
async def chat_stdio(query:str):
    async with MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["tool/math.py"],
                "transport": "stdio",
            }
        }
    ) as client:
        await client.__aenter__()
        tools = client.get_tools()
        agent = create_react_agent(model, tools)
        response = await agent.ainvoke({"messages" : query})

    return {"response":response}


@router.get("/chat_sse")
async def chat_sse(query:str):
    async with MultiServerMCPClient(
        {
        "test":{
            "url" : "http://127.0.0.1:%d/sse"%tool_port,
            "transport": "sse"
            }
        }
    ) as client:
        await client.__aenter__()
        tools = client.get_tools()
        agent = create_react_agent(model, tools)
        responses = await agent.ainvoke({"messages" : query})
        message_handler = MessageHandler(responses)
        message_handler.save_as_json()

    return {"response":responses}
