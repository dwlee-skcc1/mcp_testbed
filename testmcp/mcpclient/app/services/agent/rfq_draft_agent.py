from typing import Any, Union, List, Dict

from services.agent.state import State
from services.agent.base_agent import BaseAgent

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI

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
        workflow.add_edge(START, "rfq_draft")
        workflow.add_edge("rfq_draft", END)
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
