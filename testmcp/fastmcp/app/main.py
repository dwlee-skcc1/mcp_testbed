from mcp.server.fastmcp import FastMCP
from fastmcp.prompts.base import UserMessage
from mcp.types import TextContent
from typing import List, Optional

from SearchRdb import search_rdb_main
from SearchDocs import search_docs_main
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
    return search_rdb_main(query)

@mcp.tool()
def search_docs(
    folder_names: list,
    keywords: Optional[list] = None,
    doc_type: Optional[str] = None,
    search_in_content: bool = False
) -> list:
    """
    문서 검색 도구 - 지정된 폴더에서 문서를 검색합니다.
    
    :param folder_names: 검색할 폴더 이름 리스트 (예: ['MR24010002M', 'MR24010003M'])
    :param keywords: 검색할 키워드들 (파일 이름에 포함되어야 하는 단어들)
    :param doc_type: 문서 형식 (예: 'docx', 'xlsx', 'pdf')
    :param search_in_content: 파일 내용 검색 여부 (기본값: False)
    :return: 검색된 파일 정보의 리스트
    """
    # search_docs 함수를 직접 호출하여 결과 반환
    return search_docs_main(
        folder_names=folder_names,
        keywords=keywords,
        doc_type=doc_type,
        search_in_content=search_in_content
    )

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