from celery import shared_task

@shared_task(name="add")
def add(a: int, b: int) -> int:
    """두 숫자를 더하는 함수"""
    return a + b

@shared_task(name="multiply")
def multiply(a: int, b: int) -> int:
    """두 숫자를 곱하는 함수"""
    return a * b

@shared_task(name="subtract")
def subtract(a: int, b: int) -> int:
    """첫 번째 숫자에서 두 번째 숫자를 빼는 함수"""
    return a - b

@shared_task(name="divide")
def divide(a: int, b: int) -> float:
    """첫 번째 숫자를 두 번째 숫자로 나누는 함수"""
    if b == 0:
        raise ValueError("0으로 나눌 수 없습니다")
    print(f"DIVIDE DEBUG: a={a}, b={b}, result={a / b}")
    return a / b