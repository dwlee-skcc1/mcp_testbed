from mcp.server.fastmcp import FastMCP
from fastmcp.prompts.base import UserMessage
from mcp.types import TextContent

from search_rdb import search_rdb
from docxtohtml import docx_to_html_main


mcp = FastMCP("test")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b

@mcp.tool()
def search_rdb(query: str) -> list[TextContent]:
    """
    Search the relational database using natural language query.
    
    Args:
        query: Natural language query to search the database
    """
    return search_rdb(query)


@mcp.tool()
def docx_to_html(file_paths: list[str]) -> str:
    """Word 문서를 HTML로 변환 
    
    Args:
        file_paths (list[str]): 변환할 Word 문서들의 경로 리스트 
        
    Returns:
        str: 변환된 HTML string
    """
    return docx_to_html_main(file_paths)






if __name__ == "__main__":
    mcp.run(transport='sse')