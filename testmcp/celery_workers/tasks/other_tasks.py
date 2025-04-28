from celery_workers.celery_app import app
from typing import Dict, Any, List

@app.task(name="celery_workers.tasks.other_tasks.example_task")
def example_task(param1: str, param2: int = 0) -> Dict[str, Any]:
    """예시 태스크"""
    return {
        "param1": param1,
        "param2": param2,
        "result": f"{param1} - {param2}"
    }

# 향후 확장성을 위한 기타 태스크 템플릿
@app.task(name="celery_workers.tasks.other_tasks.process_data")
def process_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """데이터 처리 태스크 템플릿"""
    # 여기에 실제 데이터 처리 로직 구현
    result = {"processed_items": len(data), "summary": "Data processed successfully"}
    return result