from fastapi import APIRouter
import os
from dotenv import load_dotenv
from pathlib import Path
from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.mcp_response import MessageHandler

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

<<<<<<< HEAD
#키워드 추출 프롬프트
keyword_extraction_prompt = """
당신은 유저 쿼리에서 문서 검색에 필요한 핵심 키워드와 파라미터를 추출한 후, 적절한 도구를 호출하는 전문가입니다.

1. 먼저 사용자의 쿼리를 분석하여 다음 정보를 추출하세요:
   - keyword: 검색할 주요 키워드 (예: 열교환기)
   - doc_type: 문서 유형 (예: RFQ)
   - author: 문서 작성자 (있는 경우)
   - project: 관련 프로젝트나 고객 (있는 경우)
   - date_after: 특정 날짜 이후 문서 (YYYY-MM-DD 형식)
   - date_before: 특정 날짜 이전 문서 (YYYY-MM-DD 형식)
   - date_range_years: 최근 N년 이내 문서 (숫자)
   - limit: 검색 결과 개수 제한 (숫자)
   - sort_by: 정렬 기준 (date, relevance 등)
   - sort_order: 정렬 순서 (desc, asc)
   - path: 검색 경로 (있는 경우)

2. 추출한 정보를 JSON 형식으로 구성하세요. 값이 없는 경우 null로 설정하세요.

3. 구성된 JSON 파라미터로 파일 검색 tool를 호출하세요.

4. 도구의 결과를 사용자에게 이해하기 쉽게 설명하세요.
"""  


@router.get("/test")
def testest():
    res = save_response_to_file("")
    return {"message":res}
=======
>>>>>>> main

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
        agent = create_react_agent(model, tools, prompt=keyword_extraction_prompt)
        responses = await agent.ainvoke({"messages" : query})
        message_handler = MessageHandler(responses)
        message_handler.save_as_json()
    return {"response":responses}
