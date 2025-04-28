from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from fastapi_server.services.schemas.chat.request import OpenAIRequest
from fastapi_server.services.agent.sample_agent import SampleAgent, SampleConnectAgent
from fastapi_server.core.llm import get_model


class SampleService:
    """샘플 서비스 클래스"""
    
    def __init__(self):
        pass

    def convert_openai_messages_to_langchain(
        self, messages: List[dict]
    ) -> List[BaseMessage]:
        """OpenAI 형식의 메시지를 Langchain 형식으로 변환"""
        converted_messages = []
        for msg in messages:
            if msg["role"] == "user":
                converted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                last_agent_response = msg["content"].split("**:")[-1]
                converted_messages.append(AIMessage(content=last_agent_response))
            elif msg["role"] == "system":
                converted_messages.append(SystemMessage(content=msg["content"]))
        return converted_messages
    
    async def tool_test(
            self,
            tools: List[str]
    ) -> Dict:
        """도구 연결 테스트"""
        # SampleConnectAgent 생성 및 그래프 초기화
        connect_agent = SampleConnectAgent()
        graph = await connect_agent.get_graph()
        
        # 초기 상태 설정
        state = await self._initialize_chat_state(
            messages=[],
            user_query="",
            tools=tools)
        
        # 그래프 실행
        responses = await self._generate_responses(state, graph)
        return {"answer": str(responses["answer"])}

    async def chat_test_completion(
        self,
        tools: List[str],
        request: OpenAIRequest
    ) -> Dict:
        """
        채팅 완료 처리

        Args:
            tools: 사용할 도구 목록
            request: 채팅 요청

        Returns:
            Dict: 응답 데이터
        """
        messages = request.messages
        
        # 시스템 메시지가 없으면 추가
        if not any(msg.get("role") == "system" for msg in messages):
            messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        
        # OpenAI 메시지를 Langchain 형식으로 변환
        langchain_messages = self.convert_openai_messages_to_langchain(messages)
        messages_list = [(msg.type, msg.content) for msg in langchain_messages]

        # 초기 상태 설정
        state = await self._initialize_chat_state(
            messages=messages_list,
            user_query=request.messages[-1]["content"],
            tools=tools)
        
        # SampleAgent 생성 및 그래프 초기화
        agent = SampleAgent(llm=get_model())
        graph = await agent.get_graph()
        
        # 응답 생성
        responses = await self._generate_responses(state, graph)
        return {"answer": str(responses["answer"])}
    
    async def _initialize_chat_state(
        self, messages: list, user_query: str, tools: List[str]
    ) -> Dict:
        """초기 상태 생성"""
        state = {
            "user_query": user_query,
            "messages": messages,
            "tool": tools,
            "answer": ""
        }
        return state

    async def _generate_responses(self, state: Dict, graph: Any) -> Dict:
        """그래프 실행 및 응답 생성"""
        responses = await graph.ainvoke(state)
        return responses