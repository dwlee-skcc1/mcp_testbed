from fastapi import APIRouter
import os
from dotenv import load_dotenv
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.mcp_response import MessageHandler

from datetime import datetime

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))


from langchain_openai import AzureChatOpenAI
model = AzureChatOpenAI(
    azure_deployment=os.getenv("OPENAI_DEPLOYMENT"),
    azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
    api_version=os.getenv("OPENAI_API_VERSION"),
    api_key=os.getenv("OPENAI_API_KEY"),
    n=1,
    temperature=0,
    max_tokens=500,
    model=os.getenv("OPENAI_MODEL"),
    verbose=True,
    streaming=False,
    )

router = APIRouter(prefix="/service")


@router.get("/chat_stdio")
async def chat_stdio(query:str):
    async with MultiServerMCPClient(
        {
            "math": {
                "command": "python",
                "args": ["tool/mathr.py"],
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