# # mcp_server/decorators.py (필요한 부분만 수정)
# class ToolDecorator:
#     def __init__(self, tool_name: str, description: str, queue: str = "default"):
#         self.tool_name = tool_name
#         self.description = description
#         self.queue = queue
    
#     def __call__(self, func):
#         # 여기서 함수 메타데이터만 등록
#         # 실제 실행은 Celery에 위임
#         func._tool_name = self.tool_name
#         func._description = self.description
#         func._queue = self.queue
#         return func

from functools import wraps
from typing import Dict, Any, Optional, Callable, List
import inspect

# 등록된 도구 목록
REGISTERED_TOOLS = []

def ToolDecorator(
    tool_name: str, 
    description: str, 
    queue: str = "default",
    version: str = "1.0"
):
    """확장된 도구 등록 데코레이터"""
    def decorator(func: Callable):
        # 함수 시그니처 분석
        sig = inspect.signature(func)
        
        # 파라미터 정보 추출
        properties = {}
        required = []
        
        for param_name, param in sig.parameters.items():
            # self 파라미터 제외
            if param_name == "self":
                continue
                
            # 기본값 & 타입 힌트 추출
            has_default = param.default != inspect.Parameter.empty
            param_type = "any"
            
            # 타입 힌트가 있는 경우 처리
            if param.annotation != inspect.Parameter.empty:
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == str:
                    param_type = "string"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list or param.annotation == List:
                    param_type = "array"
                elif param.annotation == dict or param.annotation == Dict:
                    param_type = "object"
            
            # 파라미터 정보 저장
            properties[param_name] = {"type": param_type}
            
            # 기본값이 없는 파라미터는 필수로 지정
            if not has_default:
                required.append(param_name)
        
        # 도구 정보
        tool_info = {
            "name": tool_name,
            "description": description or func.__doc__ or "",
            "version": version,
            "args_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            },
            "queue": queue
        }
        
        # 함수에 도구 정보 저장
        func._tool_info = tool_info
        
        # 도구 목록에 추가
        REGISTERED_TOOLS.append(tool_info)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        return wrapper
    
    return decorator