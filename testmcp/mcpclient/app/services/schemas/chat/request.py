from typing import List, Optional

from pydantic import BaseModel

class OpenAIRequest(BaseModel):
    messages: list
    max_tokens: Optional[int] = None
    temperature: float = 0.1
    stop: Optional[List[str]] = None
    n: int = 1
    stream: bool = False