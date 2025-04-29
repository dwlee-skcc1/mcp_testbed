from typing import Any, Union, List, Dict

from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from utils.mcp_response import MessageHandler
from tools.tool_manager import ToolManager




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
        server_params = {tool : tool_parameters[tool] for tool in state["tool"]}
        
        async with MultiServerMCPClient(server_params) as client:
            await client.__aenter__()
            tools = client.get_tools()
        tool_spec = []
        for tool in tools:
            input_params = ["%s:%s"%(k, v["type"]) for k, v in tool.args_schema["properties"].items()]
            tool_spec.append("%s(%s) : %s"%(tool.name, ", ".join(input_params), tool.description))

        state["answer"] = "\n".join(tool_spec)
        return state





class SampleAgent(BaseAgent):
    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        super().__init__(llm)
    
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
        tool_parameters = tool_manager.get_tool_parameters(state["tool"])
        async with MultiServerMCPClient(
            {tool : tool_parameters[tool] for tool in state["tool"]}
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

