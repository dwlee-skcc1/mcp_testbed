from pathlib import Path
import os
import json
from dotenv import load_dotenv
from typing import Dict, Union, List

# 환경 변수 로드
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

# 서버 설정 가져오기
client_port = int(os.getenv("CLIENT_PORT", 8000))
tool_port = int(os.getenv("TOOL_PORT", 8001))
mcp_server_host = os.getenv("MCP_SERVER_HOST", "mcp_server")  # Docker 컴포즈에서 사용하는 서비스 이름

# 도구 디렉토리 설정
tool_dir = Path(__file__).resolve().parent

class ToolManager:
    """도구 설정 관리 클래스"""
    
    def __init__(self):
        # 도구 설정 파일 로드
        tools_file = os.path.join(tool_dir, "tools.json")
        
        # 설정 파일이 없으면 기본 설정 파일 생성
        if not os.path.exists(tools_file):
            self._create_default_tools_file(tools_file)
        
        # 설정 파일 로드
        try:
            with open(tools_file, "r", encoding="utf-8") as f:
                self.tools = json.load(f)
        except Exception as e:
            print(f"도구 설정 파일 로드 오류: {str(e)}")
            self.tools = self._get_default_tools()
        
        self.tool_list = list(self.tools.keys())

    def _get_default_tools(self) -> Dict[str, Dict]:
        """기본 도구 설정 반환"""
        return {
            "math": {
                "transport": "sse",
                "url": f"http://{mcp_server_host}:{tool_port}",
                "args": []
            },
            "sse": {
                "transport": "sse",
                "url": f"http://{mcp_server_host}:{tool_port}",
                "args": []
            },
            "stdio": {
                "transport": "stdio",
                "args": ["math_tool.py"]
            }
        }
    
    def _create_default_tools_file(self, file_path: str):
        """기본 도구 설정 파일 생성"""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._get_default_tools(), f, indent=4)

    def get_list(self) -> List[str]:
        """도구 목록 반환"""
        return self.tool_list
    
    def get_tool_parameters(self, tools: List[str]) -> Dict:
        """도구별 파라미터 반환"""
        tool_params = {}
        
        for tool in tools:
            try:
                params = self.tools[tool].copy()
                
                # localhost를 mcp_server로 교체 (안전장치) - 이 부분 추가
                if params["transport"] == "sse" and "url" in params and "localhost" in params["url"]:
                    params["url"] = params["url"].replace("localhost", mcp_server_host)
                
                # 도구 유형에 따른 파라미터 처리
                if params["transport"] == "sse":
                    # SSE 도구는 URL 형식 확인
                    if not params["url"].endswith("/sse"):
                        params["url"] += "/sse"
                elif params["transport"] == "stdio":
                    # stdio 도구는 경로 설정
                    if isinstance(params["args"], list) and len(params["args"]) > 0:
                        script_name = params["args"][0]
                        params["args"] = [str(tool_dir / script_name)]
                
                tool_params[tool] = params
            
            except KeyError:
                print(f"도구 설정 없음: {tool}")
                continue
        
        if not tool_params:
            return {"messages": "No valid tools found"}
        
        return tool_params