from mcp_server.decorators import ToolDecorator

@ToolDecorator(tool_name="add", description="두 숫자를 더합니다", queue="math_queue")
def add(a: int, b: int) -> int:
    """두 숫자를 더하는 함수"""
    # 실제 구현은 Celery Worker에서 처리
    # 여기서는 인터페이스만 정의
    pass

@ToolDecorator(tool_name="multiply", description="두 숫자를 곱합니다", queue="math_queue")
def multiply(a: int, b: int) -> int:
    """두 숫자를 곱하는 함수"""
    # 실제 구현은 Celery Worker에서 처리
    pass

@ToolDecorator(tool_name="subtract", description="첫 번째 숫자에서 두 번째 숫자를 뺍니다", queue="math_queue")
def subtract(a: int, b: int) -> int:
    """첫 번째 숫자에서 두 번째 숫자를 빼는 함수"""
    # 실제 구현은 Celery Worker에서 처리
    pass

@ToolDecorator(tool_name="divide", description="첫 번째 숫자를 두 번째 숫자로 나눕니다", queue="math_queue")
def divide(a: int, b: int) -> float:
    """첫 번째 숫자를 두 번째 숫자로 나누는 함수"""
    # 실제 구현은 Celery Worker에서 처리
    pass