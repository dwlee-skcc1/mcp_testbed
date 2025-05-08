from fastapi import APIRouter
import json, os
from dotenv import load_dotenv
from pathlib import Path

from services.agent.rfq_draft_agent import RfqDraftAgent, RfqDraftAgent1
from services.rfq_draft_service import RfqDraftService
from services.agent.module1_agent import Module1Agent
from services.sample_service import SampleService
from services.schemas.chat.request import OpenAIRequest
from core.llm import get_model

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent.parent / "tools" 
file_dir = Path(__file__).resolve().parent.parent / "data" / "sample_document_1.md"
sample_step_dir = Path(__file__).resolve().parent.parent / "data" / "sample_step.json"

router = APIRouter()


@router.post("/connect")
async def connect():
    """
    connect to document tool
    """

    service = SampleService()
    graph = await RfqDraftAgent(llm=get_model()).get_graph()
    tools = await service.tool_test(tools=["rfq_draft"], graph=graph)
    return tools["answer"]

@router.post("/get_rfq_draft")
async def get_rfq_draft(request:OpenAIRequest):
    """
    get rfq draft
    """
    service = RfqDraftService()
    graph = await RfqDraftAgent(llm=get_model()).get_graph()
    return await service.get_rfq_draft(request=request, graph=graph)

@router.post("/get_rfq_draft_wo_agent")
def get_rfq_draft_wo_agent(request:OpenAIRequest):
    """
    get rfq draft without react agent
    """
    service = RfqDraftService()
    graph = RfqDraftAgent1(llm=get_model()).get_graph()
    return service.get_rfq_draft_wo_agent(request=request, graph=graph)
