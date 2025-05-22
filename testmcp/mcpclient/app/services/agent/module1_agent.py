from typing import Any, Union, List, Dict


from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from utils.mcp_response import MessageHandler
from tools.tool_manager import ToolManager


class Module1Agent(BaseAgent):
    def __init__(self):
        pass
        
    async def get_graph(self):
        workflow = StateGraph(State)
        workflow.add_node("module1", self.run_module1)
        workflow.add_edge(START, "module1")
        workflow.add_edge("module1", END)
        return workflow.compile()
    
    async def run_module1(
            self,
            state:Dict
            ):

        state["user_query"] = state.get("user_query")
        state["messages"] = state.get("messages")
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
    
    async def get_tool_spec(self, tools:List[str]):
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(tools)
        server_params = {tool : tool_parameters[tool] for tool in tools}
        async with MultiServerMCPClient(server_params) as client:
            await client.__aenter__()
            tools = client.get_tools()
        
        tool_spec = []
        for tool in tools:
            input_params = ["%s:%s"%(k, v["type"]) for k, v in tool.args_schema["properties"].items()]
            tool_spec.append("%s(%s) : %s"%(tool.name, ", ".join(input_params), tool.description))
        return tool_spec
