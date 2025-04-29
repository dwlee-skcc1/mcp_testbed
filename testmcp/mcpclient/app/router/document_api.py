from fastapi import APIRouter
import json, os
from dotenv import load_dotenv
from pathlib import Path

from services.agent.document_agent import DocumentAgent
from services.sample_service import SampleService
from core.llm import get_model


ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent.parent / "tools" 



router = APIRouter()


@router.post("/connect")
async def connect():
    """
    connect to document tool
    """

    service = SampleService()
    graph = await DocumentAgent(llm=get_model()).get_graph()
    tools = await service.tool_test(tools=["document"], graph=graph)
    return tools["answer"]