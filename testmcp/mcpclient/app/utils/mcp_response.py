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
                    "content": msg.content.replace("\\", ""),
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
                }, file, indent=4, ensure_ascii=False)
        return

    def get_answer(self):
        return self.sturctured_messages[-1]["content"]