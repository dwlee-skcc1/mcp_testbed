from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

class SampleResponse(BaseModel):
    """샘플 응답 스키마"""
    answer: str = Field(..., description="에이전트 응답")