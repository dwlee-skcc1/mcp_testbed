from typing import Any, Dict, Optional, Union, List
import json
import re

from langchain_openai import AzureChatOpenAI, ChatOpenAI
from celery_workers.tools.tool_manager import ToolManager
from fastapi_server.client.mcp_client import MultiServerMCPClient

class BaseAgent:
    """기본 에이전트 클래스"""

    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        self.llm = llm
        self.tool_manager = ToolManager() #tool manager 초기화
        
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
        
    async def execute_tool(self, tool_name: str, args: Dict[str, Any], tool_parameters: Dict) -> Any:
        """도구 실행"""
        try:
            async with MultiServerMCPClient(tool_parameters) as client:
                result = await client.execute_tool(tool_name, **args)
                print(f"도구 '{tool_name}' 실행 결과: {result}")
                return result
        except Exception as e:
            print(f"도구 실행 오류: {str(e)}")
            return {"error": str(e)}
    
    def extract_tool_calls(self, llm_response: str) -> List[Dict]:
        """LLM 응답에서 도구 호출 정보 추출"""
        # 도구 호출 패턴 예: tool_name(param1=value1, param2=value2)
        pattern = r'(\w+)\(([^)]*)\)'
        matches = re.findall(pattern, llm_response)
        
        tool_calls = []
        for tool_name, args_str in matches:
            args = {}
            if args_str.strip():
                # 인자 파싱 (예: a=10, b=20 -> {"a": 10, "b": 20})
                for arg in args_str.split(','):
                    if '=' in arg:
                        key, value = arg.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 숫자 타입 변환
                        if value.isdigit():
                            value = int(value)
                        elif value.replace('.', '', 1).isdigit() and value.count('.') <= 1:
                            value = float(value)
                        # 문자열에서 따옴표 제거
                        elif (value.startswith('"') and value.endswith('"')) or \
                             (value.startswith("'") and value.endswith("'")):
                            value = value[1:-1]
                            
                        args[key] = value
            
            tool_calls.append({
                "tool_name": tool_name,
                "args": args
            })
        
        return tool_calls