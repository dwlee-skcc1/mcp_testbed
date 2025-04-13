from pathlib import Path
import os, json
from dotenv import load_dotenv

ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))

tool_dir = Path(__file__).resolve().parent.parent / "tool" 

class ToolManager:
    def __init__(self):
        self.tools = json.load(
            open(os.path.join(tool_dir, "tools.json"), "r", encoding="utf-8"))
        self.tool_list = list(self.tools.keys())

    def get_list(self):
        return self.tool_list
    
    def get_tool_parameters(self, tool:str):
        try:
            tool_params = self.tools[tool]
            if tool_params["transport"] == "sse":
                tool_params["url"] += ":%d/sse"%tool_port
            else:
                tool_params["args"][0] = f"{tool_dir}/%{tool_params["args"]}"
            return tool_params
        
        except KeyError as e:
            # raise error
            return {"messages" : "There is no tool for %s"%tool}