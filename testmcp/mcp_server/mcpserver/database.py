from fastmcp import FastMCP
from pydantic import BaseModel, Field

database_mcp = FastMCP("DatabaseServer")

class EchoInput(BaseModel):
    message: str = Field(..., description="에코할 메시지", min_length=1, max_length=100)
    repeat: int = Field(1, description="메시지를 반복할 횟수", ge=1, le=10)
    language: str = Field("ko", description="응답 언어 코드(예: 'ko', 'en')")

@database_mcp.tool(description="A more advanced echo tool")
def echo(input: EchoInput) -> str:
    result = (f"Echo: {input.message} " * input.repeat).strip()
    if input.language == "en":
        return result.replace("Echo", "Echo (EN)")
    return result

database_app = database_mcp.http_app()