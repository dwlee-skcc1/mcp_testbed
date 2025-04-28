from typing import List, Dict, Optional, Any, Sequence
from typing_extensions import TypedDict

class State(TypedDict, total=False):
    """에이전트 상태 정의"""
    user_query: str
    messages: List[Dict[str, Any]]  # 대화 메시지 (Langchain 형식 또는 OpenAI 형식)
    tool: List[str]  # 사용할 도구 이름 목록
    answer: str  # 최종 답변