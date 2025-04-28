from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

class OpenAIRequest(BaseModel):
    """OpenAI API 형식의 채팅 요청"""
    messages: List[Dict[str, Any]] = Field(..., description="대화 메시지 목록")
    max_tokens: Optional[int] = Field(None, description="최대 토큰 수")
    temperature: float = Field(0.1, description="온도 (창의성)")
    stop: Optional[List[str]] = Field(None, description="중지 토큰 목록")
    n: int = Field(1, description="생성할 답변 수")
    stream: bool = Field(False, description="스트리밍 여부")