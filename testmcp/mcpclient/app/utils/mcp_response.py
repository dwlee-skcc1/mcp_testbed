import json, os
from pathlib import Path
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

class MessageHandler:
    def __init__(self, messages):
        self.messages = None
        self.sturctured_messages = []
        try:
            self.messages = messages["messages"]
        except KeyError as e:
            self.messages = messages
        
        self.total_token_usage = 0
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                self.sturctured_messages.append({
                    "type": "human",
                    "content": msg.content})
            elif isinstance(msg, AIMessage):
                self.sturctured_messages.append({
                    "type": "ai",
                    "content": msg.content.rpelace("\\", ""),
                    "tool_calls" : [tool["name"] for tool in msg.tool_calls],
                    "token_usage" : msg.usage_metadata["total_tokens"]
                    })
                self.total_token_usage += int(msg.usage_metadata["total_tokens"])
            elif isinstance(msg, ToolMessage):
                self.sturctured_messages.append({
                    "type":"tool",
                    "content":msg.content,
                    "name":msg.name
                })

    def save_as_json(self):
        file_path = os.path.join(Path(__file__).absolute().parent.parent, "logs", "reponse_%s.json"%(datetime.now().strftime("%y%m%d%H%M%S")))
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump({
                "messages" : self.sturctured_messages,
                "total_token_usage" : self.total_token_usage
                }, file, indent=4)
        return



def save_response_to_file(response):
    file_path = os.path.join(Path(__file__).absolute().parent.parent, "logs", "reponse_%s.json"%(datetime.now().strftime("%y%m%d%H%M%S")))
    with open(file_path, "w", encoding="utf-8") as file:
        json_data = json.loads(str(response))
        json.dump(json_data, file, ensure_ascii=False, indent=4)
    return file_path


def mcp_response_to_dict(json_data):
    """JSON 데이터를 분석하여 단계별 도구 호출, 총 토큰 소모량 등을 정리합니다."""

    messages = json_data["response"]["messages"]
    tool_calls = []
    total_tokens = 0

    for message in messages:
        if message["type"] == "ai" and "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                tool_calls.append({
                    "name": tool_call["name"],
                    "args": tool_call["args"],
                    "id": tool_call["id"]
                })
        if "usage_metadata" in message:
            total_tokens += message["usage_metadata"]["total_tokens"]

    result = {
        "tool_calls": tool_calls,
        "total_tokens": total_tokens,
        "steps": []
    }

    step_num = 0

    for message in messages:
        step_num += 1
        if message["type"] == "human":
            
            result["steps"].append({
                "step": step_num,
                "type": "human",
                "content": message["content"]
            })
        elif message["type"] == "ai":
            if "tool_calls" in message:
                result["steps"].append({
                    "step": step_num,
                    "type": "ai",
                    "content": message["content"],
                    "tool_calls": message["tool_calls"]
                })
            else:
                result["steps"].append({
                    "step": step_num,
                    "type": "ai",
                    "content": message["content"]
                })
        elif message["type"] == "tool":
            result["steps"].append({
                "step": step_num,
                "type": "tool",
                "name": message["name"],
                "content": message["content"],
                "tool_call_id": message["tool_call_id"]
            })

    return result
