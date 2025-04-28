from pathlib import Path
import os, json
from dotenv import load_dotenv
from typing import Dict, Union, List

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent

class ToolManager:
    def __init__(self):
        self.tools = json.load(
            open(os.path.join(tool_dir, "tools.json"), "r", encoding="utf-8"))
        self.tool_list = list(self.tools.keys())

    def get_list(self):
        return self.tool_list
    
    def get_tool_parameters(
            self, 
            tools:List[str]
            )->Dict:
        tool_params = {}
        for tool in tools:
            try:
                params = self.tools[tool].copy()
                
                if params["transport"] == "sse":
                    # 기존 코드를 아래 코드로 교체
                    # params["url"] += ":%d/sse"%tool_port  # 이 코드가 제대로 작동하지 않음
                    
                    # localhost를 mcp_server로 교체 (안전장치)
                    if "localhost" in params["url"]:
                        params["url"] = params["url"].replace("localhost", "mcp_server")
                    
                    # 명시적으로 포트와 경로 추가
                    if not ":8001" in params["url"]:  # 포트가 없으면 추가
                        params["url"] += ":8001"
                    if not params["url"].endswith("/sse"):  # /sse가 없으면 추가
                        params["url"] += "/sse"
                else:
                    params["args"][0] = "%s/%s"%(tool_dir, params["args"])
                
                tool_params[tool] = params
            
            except KeyError as e:
                # raise error
                return {"messages" : "There is no tool for %s"%tool}

            return tool_params