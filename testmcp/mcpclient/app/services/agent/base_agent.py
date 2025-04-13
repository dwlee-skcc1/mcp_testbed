from typing import Any, Dict, Optional, Union
import json

from langchain_openai import AzureChatOpenAI, ChatOpenAI


class BaseAgent:
    """기본 에이전트 클래스"""

    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        self.llm = llm

    def get_graph(self) -> Any:
        """그래프 구성을 반환"""
        raise NotImplementedError

    def run_graph(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """그래프 실행"""
        graph = self.get_graph()
        return graph.invoke(state)
    
    @staticmethod
    def read_state() -> Optional[Dict[str, Any]]:
        """상태 읽기"""
        try:
            with open("state.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            ## log 제거
            print(f"파일 읽기 중 오류가 발생했습니다: {e}")
            return None