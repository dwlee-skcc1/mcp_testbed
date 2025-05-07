from pathlib import Path
import os, json
from dotenv import load_dotenv
from typing import Dict, Union, List

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent.parent / "tools" 
module1_tool_dir = tool_dir / "module1.json"

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
                params = self.tools[tool]
                print(params)
                if params["transport"] == "sse":
                    params["url"] += ":%d/sse"%tool_port
                else:
                    params["args"][0] = os.path.join(tool_dir, params["args"][0])
                tool_params[tool] = params
            
            except KeyError as e:
                # raise error
                return {"messages" : "There is no tool for %s"%tool}

            return tool_params
    
    def get_tool_list(
            self,
            tool_name:str
    )->List[Dict]:
        # db crud로 긁어온다고 생각하고 하드코딩
        tool_list = json.load(open(os.path.join(tool_dir, f"{tool_name}.json"), "r", encoding="utf-8"))
        return tool_list
    
    def get_module1_tool_list(self):
        ## 모듈1 툴 리스트 가져오기. 완전 하드코딩.
        tool_list = json.load(open(module1_tool_dir, "r", encoding="utf-8"))
        return tool_list
