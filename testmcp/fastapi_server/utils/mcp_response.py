import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Union, Optional, Sequence

from langchain_core.messages import HumanMessage, AIMessage, ToolMessage, BaseMessage


class MessageHandler:
    """LLM 응답 메시지 처리 클래스"""
    
    def __init__(self, messages):
        self.messages = None
        self.structured_messages = []
        self.total_token_usage = 0
        
        # messages 형식에 따라 처리
        if isinstance(messages, dict) and "messages" in messages:
            self.messages = messages["messages"]
        else:
            self.messages = messages
        
        self._process_messages()
    
    def _process_messages(self):
        """메시지 처리 및 구조화"""
        if not self.messages:
            return
        
        for msg in self.messages:
            if isinstance(msg, HumanMessage):
                self.structured_messages.append({
                    "type": "human",
                    "content": msg.content
                })
            elif isinstance(msg, AIMessage):
                # 토큰 사용량 추출
                token_usage = 0
                if hasattr(msg, 'usage_metadata') and msg.usage_metadata:
                    token_usage = msg.usage_metadata.get("total_tokens", 0)
                    self.total_token_usage += int(token_usage)
                
                # 도구 호출 정보 추출
                tool_calls = []
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_calls = [tool.get("name", "unknown_tool") for tool in msg.tool_calls if isinstance(tool, dict)]
                
                self.structured_messages.append({
                    "type": "ai",
                    "content": msg.content.replace("\\", "") if msg.content else "",
                    "tool_calls": tool_calls,
                    "token_usage": token_usage
                })
            elif isinstance(msg, ToolMessage):
                self.structured_messages.append({
                    "type": "tool",
                    "content": msg.content,
                    "name": getattr(msg, 'name', None) or getattr(msg, 'tool_call_id', 'unknown')
                })
            elif isinstance(msg, dict):  # Langchain 메시지 객체가 아닌 일반 dict인 경우
                msg_type = msg.get("type", "unknown")
                self.structured_messages.append({
                    "type": msg_type,
                    "content": msg.get("content", ""),
                    **{k: v for k, v in msg.items() if k not in ["type", "content"]}
                })
            else:
                # 기타 메시지 타입
                self.structured_messages.append({
                    "type": getattr(msg, "type", "unknown"),
                    "content": str(getattr(msg, "content", msg))
                })

    def save_as_json(self):
        """응답을 JSON 파일로 저장"""
        try:
            # 로그 디렉토리 생성
            logs_dir = Path(__file__).absolute().parent.parent.parent / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            # 파일 이름 생성 (타임스탬프 포함)
            timestamp = datetime.now().strftime("%y%m%d%H%M%S")
            file_path = logs_dir / f"response_{timestamp}.json"
            
            # JSON 파일 저장
            with open(file_path, "w", encoding="utf-8") as file:
                json.dump({
                    "messages": self.structured_messages,
                    "total_token_usage": self.total_token_usage
                }, file, indent=4)
            
            print(f"Response saved to {file_path}")
        except Exception as e:
            print(f"Failed to save response: {str(e)}")
        return

    def get_answer(self) -> str:
        """최종 답변 텍스트 추출"""
        if not self.structured_messages:
            return "No response data available."
        
        # 마지막 메시지가 AI 메시지인 경우 그 내용을 반환
        last_msg = self.structured_messages[-1]
        if last_msg.get("type") == "ai":
            return last_msg.get("content", "")
        
        # 마지막 메시지가 AI 메시지가 아니면 마지막 AI 메시지 찾기
        for msg in reversed(self.structured_messages):
            if msg.get("type") == "ai":
                return msg.get("content", "")
        
        # AI 메시지가 없는 경우
        return "No AI response found."