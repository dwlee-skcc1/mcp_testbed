from typing import Any, Union, List, Dict

from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from utils.mcp_response import MessageHandler
from tools.tool_manager import ToolManager
from services.schemas.chat.response import RfqDraftResponse

class RfqDraftAgent(BaseAgent):
    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        super().__init__(llm)
    
    async def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("rfq_draft", self.run_rfq_draft)
        workflow.add_node("form_structured_output", self.form_structured_output)
        workflow.add_edge(START, "rfq_draft")
        workflow.add_edge("rfq_draft", "form_structured_output")
        workflow.add_edge("form_structured_output", END)
        return workflow.compile()

    async def run_rfq_draft(
            self,
            state: Dict
            ):
        state["user_query"] = state.get("user_query")
        state["messages"] = state.get("messages")
        

        #tool = ["document"]로 고정
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(state["tool"])
        server_params = {tool: tool_parameters[tool] for tool in state["tool"]}

        async with MultiServerMCPClient(server_params) as client:
            await client.__aenter__()
            tools = client.get_tools()
            agent = create_react_agent(
                self.llm,
                tools,
                response_format=RfqDraftResponse
            )
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant that processes and analyzes documents."},
                {"role": "user", "content": state["user_query"]}
            ]
            
            responses = await agent.ainvoke({"messages": messages})
            message_handler = MessageHandler(responses)
            message_handler.save_as_json()
            answer = message_handler.get_answer()
            state["answer"] = answer

        return state
    
    async def form_structured_output(
            self,
            state:Dict
    ):
        tool_manager = ToolManager()
        tools_module1 = tool_manager.get_module1_tool_list()# keys : name, description
        available_tools_str = ""
        for tool in tools_module1:
            available_tools_str += f"{tool['name']} : {tool['description']}\n"

        prompt = f"""아래 내용을 바탕으로 structured output으로 변환해주세요.
        내용 : {state.get("answer")}
        제공된 함수들: {available_tools_str}
        """
        chat_messages=[
            {"role": "system", "content": "You are a helpful assistant that processes and analyzes documents."},
            {"role": "user", "content": prompt}
        ]
        structured_llm = self.llm.with_structured_output(RfqDraftResponse)
        response = await structured_llm.ainvoke(
            chat_messages
        )
        response_json = response.model_dump_json()
        state["answer"] = str(response_json)

        return state

from pathlib import Path
import markdown
file_dir = Path(__file__).resolve().parent.parent / "data" / "sample_document_0.md"

class RfqDraftAgent1(BaseAgent):
    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        super().__init__(llm)

    @staticmethod
    def read_markdown_file(file_path:str=file_dir):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            # Parse markdown content to HTML
            html_content = markdown.markdown(content)
            return html_content
        except FileNotFoundError:
            print(f"Error: File not found at path: {file_path}")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
    
    def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("rfq_draft", self.run_rfq_draft)
        workflow.add_edge(START, "rfq_draft")
        workflow.add_edge("rfq_draft", END)

    def rfq_draft(self, state:Dict):


        tool_manager = ToolManager()
        tools_module1 = tool_manager.get_module1_tool_list()# keys : name, description
        available_tools_str = ""
        for tool in tools_module1:
            available_tools_str += f"{tool['name']} : {tool['description']}\n"
        
        document = self.read_markdown_file()

        prompt = f"""아래 문서의 내용을 절차지향적으로 정리하고, 제공된 함수들을 최대한 활용할 수 있는 step-action 구조로 작성해줘.
        이 때, step의 갯수는 최대 5개를 넘지 않으며 각 step에는 여러 개의 action으로 구성 될 수 있어.
        그리고 각 action들은 하나의 tool을 사용할거야. tool을 작성할 때는 함수 이름으로만 작성해줘.
        문서내용: {document}
        제공된 함수들: {available_tools_str}
        사용자 질문: {state.get("user_query")}
        """



        return
