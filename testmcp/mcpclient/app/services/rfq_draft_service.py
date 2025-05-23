from typing import Any, Dict, List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from services.schemas.chat.request import OpenAIRequest
from tools.tool_manager import ToolManager
from langchain_mcp_adapters.client import MultiServerMCPClient

from pathlib import Path

data_dir = Path(__file__).resolve().parent.parent / "data"


class RfqDraftService:
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
    
    async def get_rfq_draft(
            self,
            request: OpenAIRequest,
            graph:Any
    ) -> Dict:
        
        # 툴 리스트 가져오기
        tool_manager = ToolManager()
        tools_module1 = tool_manager.get_module1_tool_list()# keys : name, description

        # 메시지 초기화
        messages = request.messages
        
        # Find last user message by iterating messages in reverse
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_query = msg["content"]
                # prompt engineering
                prompt = self._prompt_engineering(
                    user_query = user_query,
                    available_tools=tools_module1,
                    file_path=data_dir / "sample_document_0.md"
                )
                msg["content"] = prompt
        
        messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        
        # OPENAI to Langchain 변환
        messages = self.convert_openai_messages_to_langchain(messages)
        messages_list = [(msg.type, msg.content) for msg in messages]

        state = self._initialize_chat_state(
            messages=messages_list, 
            user_query=request.messages[-1]["content"],
            tools=["document"]
        )

        # 응답 생성
        responses = await self._generate_responses(state, graph) #state 객체로 나옴 
        return {"answer" : str(responses["answer"])}
    
    def get_rfq_draft_wo_agent(
            self,
            request:OpenAIRequest,
            graph:Any
    ) -> Dict:
        tool_manager = ToolManager()
        tools_module1 = tool_manager.get_module1_tool_list()# keys : name, description

        # 메시지 초기화
        messages = request.messages
        
        # Find last user message by iterating messages in reverse
        for msg in reversed(messages):
            if msg["role"] == "user":
                user_query = msg["content"]
                # prompt engineering
                prompt = self._prompt_engineering(
                    user_query = user_query,
                    available_tools=tools_module1,
                    file_path=data_dir / "sample_document_0.md"
                )
                msg["content"] = prompt
        
        messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        
        # OPENAI to Langchain 변환
        messages = self.convert_openai_messages_to_langchain(messages)
        messages_list = [(msg.type, msg.content) for msg in messages]

        state = self._initialize_chat_state(
            messages=messages_list, 
            user_query=request.messages[-1]["content"],
            tools=["document"]
        )
        response = graph.invoke(state)
        print(response["answer"])
        return response
    

    def _initialize_chat_state( 
        self, messages:list, user_query:str, tools:List[str]
    )->Dict:
        state = {
            "user_query":user_query,
            "messages":messages,
            "tool":tools,
            "answer" : ""
        }
        return state
    
    async def _generate_responses(self, state: Dict, graph: Any) -> Any:
        """응답 생성"""
        # responses = []
        # async for s in graph.astream(state, stream_mode="values"):
        #     if "__end__" not in s:
        #         responses.append(s)
        responses = await graph.ainvoke(state)
        return responses
    
    @staticmethod
    def _prompt_engineering(
            user_query:str,
            available_tools:List[Dict],
            file_path:str):
        available_tools_str = ""
        for tool in available_tools:
            available_tools_str += f"{tool['name']} : {tool['description']}\n"

        prompt = f"""아래 문서의 내용을 절차지향적으로 정리하여 RFQ (Request For Quotation) 견적요청서 초안 작성 플로우차트를 구성하려고 해.
        이를 위해 제공된 아래 함수들을 최대한 활용할 수 있는 step-(action, action, ...) 구조로 작성해줘.
        이 때, step의 갯수는 최대 5개를 넘지 않아.
        *그리고 하나의 step에는 여러 개의 action으로 구성 될 수 있어.*
        각 action들은 하나의 tool을 사용할거야. tool을 작성할 때는 함수 이름으로만 작성해줘.
        문서경로: {file_path}
        제공된 함수들: {available_tools_str}
        사용자 질문: {user_query}
        """
        return prompt