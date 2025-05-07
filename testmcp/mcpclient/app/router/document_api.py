from fastapi import APIRouter
import json, os
from dotenv import load_dotenv
from pathlib import Path

from services.agent.rfq_draft_agent import RfqDraftAgent
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


# @router.post("/react")
# async def react():
#     """
#     connect to document tool
#     """
#     module1_agent = Module1Agent()
#     tools_str = await module1_agent.get_tool_spec(["module1"])

#     with open(sample_step_dir, "r", encoding="utf-8") as f:
#         sample_step = json.load(f)
#     sample_step_str = json.dumps(sample_step, ensure_ascii=False)

#     query = f"""
#     문서의 위치는 {file_dir} 입니다.
#     문서의 앞부분에서 목차를 찾고 이를 바탕으로 문서 내용을 4단계의 절차로 정리해줘.
#     이 때, 각 절차의 세부내용은 아래 tool list를 참고하여 작성해줘.
#     그 후에 문서의 body를 읽고 이를 바탕으로 앞서 정리한 4단계의 절차의 세부 내용을 정리해줘.
#     이를 바탕으로 다음과 같은 형식의 json output을 반환해줘.
#     [예시 형식]
#     {sample_step_str}
#     [tool list]
#     {tools_str}
#     """
#     request = OpenAIRequest(
#         messages=[
#             {"role": "user", "content": query}
#         ]
#     )

#     service = SampleService()
#     graph = await RfqDraftAgent(llm=get_model()).get_graph()
#     tools = await service.chat_test_completion(tools=["rfq_draft"], request=request, graph=graph)
#     return tools["answer"]