from typing import Any, Union, List, Dict

from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.runnables import RunnablePassthrough
from utils.mcp_response import MessageHandler
from tool.tool_manager import ToolManager

tool_manager = ToolManager()


def sample_tool_selector(state:State)->State:
    state["tool"] = "test"


class SampleConnectAgent(BaseAgent):
    def __init__(self):
        self.system_prompt = "You are a helpful assistant."
    
    def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("connect", self.run_sample_connect)
        workflow.add_edge(START, "connect")
        workflow.add_edge("connect", END)
        return workflow.compile()

    async def run_sample_connect(self, state:State)->State:
        
        state = sample_tool_selector(state)
        
        async with MultiServerMCPClient(
            {state["tool"] : tool_manager.get_tool_parameters(state["tool"])}
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
        sample_tool_selector(state)
        state["user_query"] = state.get("user_query")
        state["messages"] = state.get("messages")

        async with MultiServerMCPClient(
            {state["tool"] : tool_manager.get_tool_parameters(state["tool"])}
        ) as client:
            await client.__aenter__()
            tools = client.get_tools()
            agent = create_react_agent(self.llm, tools)
            responses = await agent.ainvoke({"messages":state["user_query"]})
            message_handler = MessageHandler(responses)
            message_handler.save_as_json()
            answer = message_handler.get_answer()
            state["answer"] = answer

        return state

