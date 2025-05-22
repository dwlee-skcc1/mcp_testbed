from typing import List, Optional, Dict

from pydantic import BaseModel

class OpenAIRequest(BaseModel):
    messages: List[Dict]
    max_tokens: Optional[int] = None
    temperature: float = 0.1
    stop: Optional[List[str]] = None
    n: int = 1
    stream: bool = False