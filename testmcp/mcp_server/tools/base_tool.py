from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseTool(ABC):
    """모든 도구의 기본 클래스"""
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        """도구 실행 메서드"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """도구 이름"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """도구 설명"""
        pass
    
    @property
    def queue(self) -> str:
        """작업 큐 이름"""
        return "default"