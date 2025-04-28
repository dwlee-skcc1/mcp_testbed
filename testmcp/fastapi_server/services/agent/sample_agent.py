from typing import Any, Union, List, Dict, Optional
import json
import re
import asyncio
import os

from fastapi_server.services.agent.state import State
from fastapi_server.services.agent.base_agent import BaseAgent
from fastapi_server.client.mcp_client import MultiServerMCPClient
from fastapi_server.utils.mcp_response import MessageHandler

from langgraph.graph import END, START, StateGraph
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from langgraph.prebuilt import create_react_agent

from celery_workers.tools.tool_manager import ToolManager

from pydantic import BaseModel



class SampleConnectAgent(BaseAgent): #baseAgent 상속
    """MCP 서버 연결 테스트 에이전트"""
    
    def __init__(self):
        super().__init__(None)  # LLM 필요 없음
        self.system_prompt = "You are a helpful assistant."
    
    async def get_graph(self):
        """그래프 생성"""
        workflow = StateGraph(State)
        workflow.add_node("connect", self.run_sample_connect)
        workflow.add_edge(START, "connect")
        workflow.add_edge("connect", END)
        return workflow.compile()

    async def run_sample_connect(self, state: Dict) -> Dict:
        """MCP 서버 연결 및 도구 정보 수집"""
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(state["tool"])
        
        print(f"Tool parameters for {state['tool']}: {tool_parameters}")
        try:
            print(f"Creating client with URL: {tool_parameters.get('sse', {}).get('url', 'None')}")
            async with MultiServerMCPClient(tool_parameters) as client:
                print("Client created successfully, requesting tools...")
                tools = await client.get_tools()
                print(f"Got tools response: {tools}")
                tool_spec = []
                
                # 도구 목록 처리 및 포맷팅
                if tools:
                    for tool in tools:
                        # 도구 이름과 설명 추출
                        name = tool.get("name", "Unknown")
                        desc = tool.get("description", "No description")
                        
                        # args_schema가 있는 경우 파라미터 정보 추출
                        if "args_schema" in tool and "properties" in tool["args_schema"]:
                            properties = tool["args_schema"]["properties"]
                            params = []
                            for param_name, param_info in properties.items():
                                param_type = param_info.get("type", "any")
                                params.append(f"{param_name}:{param_type}")
                            
                            tool_spec.append(f"{name}({', '.join(params)}) : {desc}")
                        else:
                            # args_schema가 없는 경우 간단한 형식으로 출력
                            tool_spec.append(f"{name} : {desc}")
                
                # 도구 목록 문자열로 변환하여 응답에 설정
                if tool_spec:
                    state["answer"] = "\n".join(tool_spec)
                    print(f"Setting answer: {state['answer']}")  # 디버깅 정보 추가
                else:
                    state["answer"] = "No tools available or empty tools response."
                    print("No tools found in response")
                    
        except Exception as e:
            import traceback
            traceback_str = traceback.format_exc()
            print(f"Error in MCP connection: {str(e)}")
            print(f"Traceback: {traceback_str}")
            state["answer"] = f"Error connecting to MCP server: {str(e)}"
        
        print(f"Final state: {state}")  # 최종 상태 출력
        return state
    


class SampleAgent(BaseAgent):
    """LLM을 사용하는 에이전트"""
    
    def __init__(self, llm: Union[ChatOpenAI, AzureChatOpenAI]):
        super().__init__(llm)
    
    async def get_graph(self):
        """에이전트 그래프 생성"""
        workflow = StateGraph(State)
        workflow.add_node("math", self.run_sample)
        workflow.add_edge(START, "math")
        workflow.add_edge("math", END)
        return workflow.compile()
    
    async def run_sample(self, state: Dict) -> Dict:
        """LLM 및 도구를 활용한 에이전트 실행"""
        user_query = state.get("user_query", "")
        messages = state.get("messages", [])
        tools = state.get("tool", [])
        
        tool_manager = ToolManager()
        tool_parameters = tool_manager.get_tool_parameters(tools)
        
        try:
            async with MultiServerMCPClient(tool_parameters) as client:
                # MCP 서버에서 도구 목록 가져오기
                mcp_tools = await client.get_tools()
                
                # LangChain 도구 형식으로 변환 (필요시)
                # converted_tools = convert_mcp_tools_to_langchain(mcp_tools)
                
                # 도구를 사용하는 에이전트 생성
                agent = create_react_agent(self.llm, mcp_tools)
                
                # 에이전트 실행
                responses = await agent.ainvoke({"messages": messages if messages else [{"type": "human", "content": user_query}]})
                
                # 응답 처리
                message_handler = MessageHandler(responses)
                message_handler.save_as_json()
                answer = message_handler.get_answer()
                state["answer"] = str(responses)#answer
        except Exception as e:
            state["answer"] = f"Error running the agent: {str(e)}"
        
        return state
    

class ToolIntegrationAgent(BaseAgent): #llm + tool 하기 위한 과정
    """도구 통합 에이전트"""
    
    def __init__(self, llm: Optional[Union[ChatOpenAI, AzureChatOpenAI]] = None):
        super().__init__(llm)
    
    async def get_graph(self):
        """에이전트 그래프 생성"""
        workflow = StateGraph(State)
        workflow.add_node("process", self.run_with_tools)
        workflow.add_edge(START, "process")
        workflow.add_edge("process", END)
        return workflow.compile()
    
    async def run_with_tools(self, state: Dict) -> Dict:
        """도구를 활용한 처리"""
        user_query = state.get("user_query", "")
        if not user_query:
            state["answer"] = "질문이 없습니다."
            return state
        
        # 도구 준비 (math 도구 사용)
        tool_queues = state.get("tool", ["math_queue"]) #math_queue는 도구 식별자(도구 그룹)
        tool_parameters = self.tool_manager.get_tool_parameters(tool_queues) #도구 그룹(math_queue)에 연결하기 위한 파라미터(서버 URL, 연결 방식)
        
        try:
            async with MultiServerMCPClient(tool_parameters) as client:
                # 1. 사용 가능한 도구 목록 가져오기
                available_tools = await client.get_tools() #client가 사용 가능 도구 목록 확인
                
                # 디버깅용 출력
                print(f"사용 가능한 도구: {available_tools}")
                
                # 2. 도구 설명 형식 구성
                tool_descriptions = []
                for tool in available_tools:
                    name = tool.get("name", "")
                    desc = tool.get("description", "")
                    properties = tool.get("args_schema", {}).get("properties", {})
                    
                    params = []
                    for param_name, param_info in properties.items():
                        param_type = param_info.get("type", "any")
                        params.append(f"{param_name}:{param_type}")
                    
                    tool_descriptions.append(f"{name}({', '.join(params)}) : {desc}")
                
                # 3. LLM에게 보낼 메시지 구성
                messages = state.get("messages", [])
                
                # 시스템 메시지 구성
                system_prompt = """
당신은 다양한 도구를 활용할 수 있는 AI 어시스턴트입니다.
필요한 경우 도구를 사용하여 사용자의 질문에 답변하세요.

다음 도구를 사용할 수 있습니다:
{tool_list}

도구를 사용하려면 다음 형식으로 작성하세요:
도구명(파라미터1=값1, 파라미터2=값2)

예시:
add(a=5, b=3)
divide(a=10, b=2)
multiply(a=4, b=5)
subtract(a=10, b=3)
"""
                
                # 메시지 목록 준비
                if not messages:
                    messages = []
                
                # 시스템 메시지 추가 또는 업데이트
                if not messages or messages[0].get("role") != "system":
                    messages.insert(0, {
                        "role": "system", 
                        "content": system_prompt.format(tool_list="\n".join(tool_descriptions))
                    })
                else:
                    messages[0]["content"] = system_prompt.format(tool_list="\n".join(tool_descriptions))
                
                # 사용자 메시지 추가
                messages.append({"role": "user", "content": user_query})
                
                # 4. LLM 호출 (self.llm이 있을 경우 사용, 없으면 외부 서비스 호출)
                llm_response = ""
                if self.llm:
                    # LangChain LLM 사용
                    response = await self.llm.ainvoke(messages)
                    llm_response = response.content
                else:
                    # 외부 API 호출 (OpenAI, Azure 등)
                    llm_response = await self._get_llm_response(messages)
                
                print(f"LLM 응답: {llm_response}")
                
                # 5. LLM 응답에서 도구 호출 추출
                tool_calls = self.extract_tool_calls(llm_response)
                
                # 6. 도구 호출이 있으면 실행
                if tool_calls:
                    print(f"도구 호출 감지: {tool_calls}")
                    
                    # 도구 호출 결과 저장
                    tool_results = []
                    
                    for call in tool_calls:
                        tool_name = call["tool_name"]
                        args = call["args"]
                        
                        # 도구가 사용 가능한지 확인
                        available_tool_names = [t.get("name") for t in available_tools]
                        if tool_name not in available_tool_names:
                            tool_results.append({
                                "tool_name": tool_name,
                                "error": f"도구 '{tool_name}'를 찾을 수 없습니다."
                            })
                            continue
                        
                        # 도구 실행
                        try:
                            result = await self.execute_tool(tool_name, args, tool_parameters)
                            tool_results.append({
                                "tool_name": tool_name,
                                "args": args,
                                "result": result
                            })
                        except Exception as e:
                            tool_results.append({
                                "tool_name": tool_name,
                                "args": args,
                                "error": str(e)
                            })
                    
                    # 도구 결과를 LLM에게 전달
                    for result in tool_results:
                        if "error" in result:
                            result_msg = f"Error: {result['error']}"
                        else:
                            # 직접 결과값만 전달
                            if isinstance(result['result'], dict) and 'result' in result['result']:
                                actual_result = result['result']['result']
                            else:
                                actual_result = result['result']
                            result_msg = f"Result: {actual_result}"
                        
                        # 도구 메시지 추가
                        messages.append({
                            "role": "function", # OpenAI 호환 형식
                            "name": result["tool_name"],
                            "content": result_msg
                        })
                    
                    # 최종 응답 생성
                    final_response = ""
                    if self.llm:
                        response = await self.llm.ainvoke(messages)
                        final_response = response.content
                    else:
                        final_response = await self._get_llm_response(messages)
                    
                    # 최종 응답 저장
                    messages.append({"role": "assistant", "content": final_response})
                    state["answer"] = final_response
                else:
                    # 도구 호출이 없으면 LLM 응답을 그대로 사용
                    messages.append({"role": "assistant", "content": llm_response})
                    state["answer"] = llm_response
                
                # 대화 기록 업데이트
                state["messages"] = messages
        
        except Exception as e:
            import traceback
            print(f"Error in ToolIntegrationAgent: {str(e)}")
            print(traceback.format_exc())
            state["answer"] = f"오류가 발생했습니다: {str(e)}"
        
        return state
    
    async def _get_llm_response(self, messages: List[Dict[str, Any]]) -> str:
        """Azure OpenAI API 호출"""
        import httpx
        import json
        
        # Azure OpenAI API 설정
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")
        api_base = os.getenv("OPENAI_API_BASE")
        if not api_base:
            raise ValueError("OPENAI_API_BASE 환경 변수가 설정되지 않았습니다.")
        api_version = os.getenv("OPENAI_API_VERSION")
        if not api_version:
            raise ValueError("OPENAI_API_VERSION 환경 변수가 설정되지 않았습니다.")
        deployment = os.getenv("OPENAI_DEPLOYMENT")
        if not deployment:
            raise ValueError("OPENAI_DEPLOYMENT 환경 변수가 설정되지 않았습니다.")
        
        # Azure용 API URL 구성
        api_url = f"{api_base}/openai/deployments/{deployment}/chat/completions?api-version={api_version}"
        
        # 메시지 형식 변환 (도구 메시지 처리)
        azure_messages = []
        for msg in messages:
            if msg["role"] == "function":
                # function 메시지를 assistant와 함수 응답으로 변환
                azure_messages.append({
                    "role": "assistant",
                    "content": f"I'll use the {msg['name']} tool"
                })
                azure_messages.append({
                    "role": "function", 
                    "name": msg["name"],
                    "content": msg["content"]
                })
            else:
                azure_messages.append(msg)
        
        # Azure OpenAI API 요청 본문
        request_body = {
            "messages": azure_messages,
            "temperature": 0.7,
            "max_tokens": 800
        }
        
        # 디버깅 정보
        print(f"Azure OpenAI API URL: {api_url}")
        # print(f"요청 헤더: api-key: {api_key[:5]}...{api_key[-5:]}")
        print(f"요청 본문: {json.dumps(request_body, ensure_ascii=False)[:200]}...")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    api_url,
                    headers={
                        "Content-Type": "application/json",
                        "api-key": api_key  # Azure OpenAI는 Authorization: Bearer 대신 api-key 헤더 사용
                    },
                    json=request_body
                )
                
                # 응답 정보 디버깅
                print(f"Azure API 응답 상태 코드: {response.status_code}")
                if response.status_code != 200:
                    print(f"응답 내용: {response.text}")
                
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_message = f"Azure OpenAI API 오류: {response.status_code} - {response.text}"
                    print(error_message)
                    return f"API 오류가 발생했습니다: {response.status_code}"
                    
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Azure API 호출 예외: {str(e)}")
            print(error_trace)
            return f"API 호출 중 오류가 발생했습니다: {str(e)}"

