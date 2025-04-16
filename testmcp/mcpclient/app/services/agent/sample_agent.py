from typing import Any, Union, List, Dict

from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from utils.mcp_response import MessageHandler
from tool.tool_manager import ToolManager



class SampleConnectAgent(BaseAgent):
    def __init__(self):
        self.system_prompt = "You are a helpful assistant."
    
    def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("connect", self.run_sample_connect)
        workflow.add_edge(START, "connect")
        workflow.add_edge("connect", END)
        return workflow.compile()

    async def run_sample_connect(
            self,
            state:Dict
            ):
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(state["tool"])
        async with MultiServerMCPClient(
            {tool : tool_parameters[tool] for tool in state["tool"]}
        ) as client:
            await client.__aenter__()
            tools = client.get_tools()
        state["answer"] = str(tools)
        return state




class SampleAgent(BaseAgent):
    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        super().__init__(llm)
        ## TBD
        self.tools = ""
        self.system_prompt = ""
    
    async def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("math", self.run_sample)
        workflow.add_edge(START, "math")
        workflow.add_edge("math", END)
        return workflow.compile()
    
    async def run_sample(
            self,
            state:Dict
            ):

        state["user_query"] = state.get("user_query")
        state["messages"] = state.get("messages")
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(state["tool"]) #tool list

        async with MultiServerMCPClient(
            {tool : tool_parameters[tool] for tool in state["tool"]}
        ) as client: #비동기로 여러 도구에 각각 client 연결
            await client.__aenter__()
            tools = client.get_tools()
            agent = create_react_agent(self.llm, tools) #react agent 생성
            responses = await agent.ainvoke({"messages":state["user_query"]}) #여기서 능동적으로 선택
            message_handler = MessageHandler(responses) #결과 메세지 파싱, 필요한 정보 뽑아내게
            message_handler.save_as_json()
            answer = message_handler.get_answer()
            state["answer"] = answer

        return state

