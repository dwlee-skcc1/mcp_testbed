from mcp_server.decorators import ToolDecorator

@ToolDecorator(tool_name="uppercase", description="텍스트를 대문자로 변환", queue="text_queue")
def uppercase(text: str) -> str:
    """입력 텍스트를 대문자로 변환합니다"""
    pass  # 실제 구현은 Celery Worker에서 처리

@ToolDecorator(tool_name="lowercase", description="텍스트를 소문자로 변환", queue="text_queue")
def lowercase(text: str) -> str:
    """입력 텍스트를 소문자로 변환합니다"""
    pass