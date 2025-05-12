# echo.py
from fastmcp import FastMCP

document_mcp = FastMCP("DocumentServer")

@document_mcp.tool(description="A simple echo tool")
def echo(message: str) -> str:
    return f"Echo: {message}"


document_app = document_mcp.http_app()



