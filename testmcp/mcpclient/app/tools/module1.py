from mcp.server.fastmcp import FastMCP

mcp = FastMCP("module1")

@mcp.tool()
def llmCustom():
    """기본 LLM"""
    pass

@mcp.tool()
def tempFileSearch():
    """폴더 내 파일 검색 (메타 데이터 필터링)"""
    pass

@mcp.tool()
def baseFileSelector():
    """문서 초안 작성을 위한 기준 파일 선정"""
    pass

@mcp.tool()
def sectionClassifier():
    """문서 구조 기반 섹션 구분"""
    pass

@mcp.tool()
def comparativeFileSelector():
    """비교 대상으로 취급할 문서 선정"""
    pass

@mcp.tool()
def documentDiff():
    """docx 문서 간 차이점 확인 (input: 두 파일의 경로)"""
    pass

@mcp.tool()
def documentGenerator():
    """초안 생성"""
    pass

@mcp.tool()
def feedbackSearch():
    """Feedback DB 내 적합한 항목 검색"""
    pass

@mcp.tool()
def canvas():
    """캔버스 출력"""
    pass

@mcp.tool()
def fileSave():
    """파일 저장"""
    pass

@mcp.tool()
def fileSaveSearch():
    """저장된 파일에서 서치"""
    pass

@mcp.tool()
def excelParser():
    """엑셀 시트를 읽고 파싱"""
    pass

@mcp.tool()
def rowMatcher():
    """문서 - 엑셀 매칭 (RFQ 특화)"""
    pass

@mcp.tool()
def excelUpdater():
    """엑셀 업데이트"""
    pass

@mcp.tool()
def sectionValidator():
    """섹션 내부 일관성 검토"""
    pass

@mcp.tool()
def crossSectionValidator():
    """섹션 간 교차 검토"""
    pass

@mcp.tool()
def missingElementChecker():
    """필수 요소 누락 검토"""
    pass

@mcp.tool()
def duplicationDetector():
    """중복 서술 검출"""
    pass

@mcp.tool()
def termChecker():
    """단위 및 용어 사용 일관성 확인"""
    pass

@mcp.tool()
def search_rdb():
    """Relational Database(postgreSQL)에서 원하는 정보 검색"""
    pass

@mcp.tool()
def search_docs():
    """폴더 내 파일 검색"""
    pass

@mcp.tool()
def doc2html():
    """문서를 html로 변환"""
    pass

if __name__ == "__main__":
    mcp.run(transport='stdio')