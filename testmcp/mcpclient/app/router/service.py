from fastapi import APIRouter, Depends, Request
import os
from dotenv import load_dotenv
from pathlib import Path

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

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



@router.get("/serv/chat")
async def chat(query:str):
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
        # tools = await load_mcp_tools(client)

    prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
            ("human", "{input}"),
        ])
        
    agent = create_react_agent(model, tools)
    response = await agent.ainvoke({"messages" : query})
    return {"response":response}