# FastMCP

FastMCP는 마이크로서비스 아키텍처에서 도구(Tool)를 쉽게 관리하고 연결할 수 있는 프레임워크입니다.

## 설치

```bash
pip install -r requirements.txt
```

> **중요**: 프로젝트에 필요한 모든 패키지는 반드시 requirements.txt에 포함되어야 합니다.

## 기능

- 여러 마이크로서비스에 분산된 도구들을 쉽게 통합
- HTTP 기반 통신으로 간편한 도구 호출
- 실시간 도구 테스트를 위한 Inspector 제공

## 시작하기

### 1. MCP 서버 만들기

각 MCP 서버는 특정 기능에 대한 도구를 제공합니다. 서버는 `mcpserver` 폴더 아래에 각각 분리하여 추가합니다.

예시 (database.py):
```python
from fastmcp import FastMCP

database_mcp = FastMCP("DatabaseServer")

@database_mcp.tool(description="A simple echo tool")
def echo(message: str) -> str:
    return f"Echo: {message}"

database_app = database_mcp.http_app()
```

### 2. 여러 MCP 서버 마운트하기

여러 MCP 서버를 하나의 애플리케이션에 마운트하려면 `main_mcp_server.py` 파일을 다음과 같이 작성합니다:

```python
from contextlib import AsyncExitStack
from fastapi import FastAPI
from starlette.routing import Mount

from mcpserver.document import document_app
from mcpserver.database import database_app

async def combined_lifespan(app):
    async with AsyncExitStack() as stack:
        # document_app의 lifespan 실행
        await stack.enter_async_context(document_app.router.lifespan_context(app))
        # database_app의 lifespan 실행
        await stack.enter_async_context(database_app.router.lifespan_context(app))
        yield

app = FastAPI(
    routes=[
        Mount("/document", app=document_app),
        Mount("/database", app=database_app),
    ],
    lifespan=combined_lifespan,
)
```

새로운 MCP 서버를 추가할 때마다 import 문과 Mount 항목을 추가하고, combined_lifespan 함수에 해당 서버의 lifespan 컨텍스트를 추가합니다.

## 테스트 방법

### 1. 웹 서버 실행

```bash
python main_mcp_server.py
```

### 2. MCP Inspector 실행

```bash
fastmcp dev main_mcp_server.py
```

Inspector는 MCP 도구를 연결하고 테스트할 수 있는 환경을 제공합니다.

### 3. Inspector에서 서버 연결

1. Inspector에서 'Streaming HTTP'를 선택합니다.
2. URL을 `http://localhost:8000/{mount_url}/mcp` 형태로 설정합니다.
   (예: `http://localhost:8000/database/mcp`)
3. Connect 버튼을 클릭합니다.

### 4. 도구 테스트

1. 'Tools' 카테고리로 이동합니다.
2. 'List Tools' 버튼을 클릭하여 사용 가능한 도구 목록을 확인합니다.
3. 원하는 도구를 선택하여 테스트합니다.

## 프로젝트 구조

```
├── mcpserver/
│   ├── document.py
│   ├── database.py
│   └── ...
├── main_mcp_server.py
└── requirements.txt
```
# LLM 사용환경 통합 가이드

## 환경 변수 설정
`.env` 파일을 프로젝트 루트에 생성하고 다음 정보를 추가합니다:

```
OPENAI_DEPLOYMENT=
OPENAI_ENDPOINT=
OPENAI_API_VERSION=
OPENAI_API_KEY=
OPENAI_MODEL=
```

## 기본 사용법

### LLM 인스턴스 가져오기

```python
from your_module import LLMSingleton

# LLM 인스턴스 가져오기
llm = LLMSingleton.get_llm()
```

### 직접 메시지 보내기

```python
from langchain_core.messages import SystemMessage, HumanMessage

# 메시지 준비
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is the capital of France?")
]

# LLM 호출
response = llm.invoke(messages)
print(response.content)
```