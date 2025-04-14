from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from services.schemas.chat.request import OpenAIRequest


class SampleService:
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
            tools:List[str],
            graph:Any
    )->Dict:
        state = await self._initialize_chat_state(
            messages=[],
            user_query="",
            tools=tools)
        responses = await self._generate_responses(state, graph)
        return {"answer" : str(responses["answer"])}

    async def chat_test_completion(
        self,
        tools:List[str],
        request: OpenAIRequest,
        graph:Any
    )->Dict:
        """
        채팅 완료 처리

        Args:
            request (OpenAIRequest): 채팅 요청
            graph: 그래프 객체

        Returns:
            Dict: 응답 데이터
        """
        messages = request.messages
        messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        
        # OPENAI to Langchain 변환
        messages = self.convert_openai_messages_to_langchain(messages)
        messages_list = [(msg.type, msg.content) for msg in messages]


        state = await self._initialize_chat_state(
            messages=messages_list,
            user_query=request.messages[-1]["content"],
            tools=tools)
        
        # 응답 생성
        responses = await self._generate_responses(state, graph) #state 객체로 나옴
        return {"answer" : str(responses["answer"])}
        # return self._create_response_data(content=str(responses["answer"]))
    
    async def _initialize_chat_state(
        self, messages:list, user_query:str, tools:List[str]
    )->Dict:
        state = {
            "user_query":user_query,
            "messages":messages,
            "tool":tools,
            "answer" : ""
        }
        return state

    async def _generate_responses(self, state: Dict, graph: Any) -> List:
        """응답 생성"""
        # responses = []
        # async for s in graph.astream(state, stream_mode="values"):
        #     if "__end__" not in s:
        #         responses.append(s)
        responses = await graph.ainvoke(state)
        return responses
    
    def _create_response_data(
        content:str
    ):
        return {
            "answer" : content
        }