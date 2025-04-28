import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
import os

from fastapi_server.services.agent.tool_callback_manager import callback_manager

class MultiServerMCPClient:
    """여러 MCP 서버에 요청을 분산하는 클라이언트"""
    
    def __init__(self, tool_configs):
        """
        Args:
            tool_configs: 도구 이름과 해당 도구를 제공하는 서버 설정을 매핑하는 딕셔너리.
                          예: {"math": {"transport": "sse", "url": "http://mcp_server:8001"}, ...}
        """
        self.tools_cache = {}
        self.client = None
        # 서버 URL 목록 수집 (중복 제거)
        self.server_urls = set(["http://mcp_server:8001"])
        
        # 문자열이나 다른 타입이 전달된 경우 처리
        if not isinstance(tool_configs, dict):
            print(f"경고: tool_configs가 딕셔너리가 아닙니다: {type(tool_configs)}, 기본 URL 사용")
            self.server_urls.add("http://mcp_server:8001/sse")
            self.tool_configs = {
                "math_queue": {
                    "transport": "sse",
                    "url": "http://mcp_server:8001/sse"
                }
            }
        else:
            self.tool_configs = tool_configs
            # 정상적인 딕셔너리 처리
            for config in tool_configs.values():
                if isinstance(config, dict) and config.get("transport") == "sse" and "url" in config:
                    self.server_urls.add(config["url"])
        
        # URL이 하나도 없으면 기본값 추가
        if not self.server_urls:
            print("서버 URL이 없습니다. 기본 URL 사용")
            self.server_urls.add("http://mcp_server:8001/sse")
    
    async def __aenter__(self):
        """비동기 컨텍스트 관리자 진입"""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 관리자 종료"""
        if self.client:
            await self.client.aclose()
            self.client = None
    
    async def get_tools(self) -> List[Dict[str, Any]]:
        """사용 가능한 도구 목록 조회"""
        if self.tools_cache:
            return list(self.tools_cache.values())
        
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        all_tools = []
        # 등록된 모든 서버에 병렬로 도구 목록 요청
        tasks = []
        for url in self.server_urls:
            tasks.append(self.client.get(f"{url}/sse/tools"))
        
        if not tasks:
            return []
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, httpx.Response) and result.status_code == 200:
                print(f"Status: {result.status_code}, URL: {result.url}")
                try:
                    # 응답 형식 처리 수정
                    response_data = result.json()
                    print(f"Response type: {type(response_data)}, Content: {response_data}")
                    # 응답이 리스트인 경우 (MCP 서버 형식)
                    if isinstance(response_data, list):
                        tools = response_data
                    # 응답이 {"tools": [...]} 형식인 경우 (다른 서버 형식)
                    elif isinstance(response_data, dict) and "tools" in response_data:
                        tools = response_data.get("tools", [])
                    else:
                        tools = []
                    
                    for tool in tools:
                        # 도구 이름으로 캐시에 저장 (동일 이름은 덮어씀)
                        if "name" in tool:
                            self.tools_cache[tool["name"]] = tool
                            all_tools.append(tool)
                except Exception as e:
                    print(f"도구 목록 파싱 오류: {str(e)}")
            elif isinstance(result, Exception):
                print(f"도구 목록 요청 오류: {str(result)}")
        
        return all_tools
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """도구 실행 요청"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        # 서버 URL 선택
        server_url = None
        for url in self.server_urls:
            server_url = url
            break
        
        if not server_url:
            raise ValueError("MCP 서버 URL을 찾을 수 없습니다.")
        
        # URL 디버깅 정보 출력
        print(f"서버 URL: {server_url}")
        
        try:
            # 서버 URL에서 끝 부분의 '/sse'를 제거 (중복 방지)
            base_url = server_url[:-4] if server_url.endswith("/sse") else server_url
            
            # FastAPI 서버 URL 및 콜백 엔드포인트 구성
            # 실제 배포 환경에서는 환경 변수 등으로 설정 필요
            fastapi_host = os.getenv("FASTAPI_HOST", "fastapi_server")
            fastapi_port = os.getenv("CLIENT_PORT", "8000")
            callback_endpoint = "/tool_callback"  # 콜백을 받을 엔드포인트
            
            # 콜백 URL 구성
            callback_url = f"http://{fastapi_host}:{fastapi_port}{callback_endpoint}"
            print(f"콜백 URL 설정: {callback_url}")
            
            # 실행 URL 구성
            run_url = f"{base_url}/sse/run"
            print(f"도구 '{tool_name}' 실행 요청 URL: {run_url}")
            
            # 실행 요청 (콜백 URL 포함)
            response = await self.client.post(
                run_url,
                json={
                    "tool_name": tool_name,
                    "args": kwargs,
                    "callback_url": callback_url
                }
            )
            
            print(f"실행 응답 상태 코드: {response.status_code}")
            
            if response.status_code in (200, 202):
                result = response.json()
                print(f"실행 응답: {result}")
                
                execution_id = result.get("execution_id")
                
                if not execution_id:
                    print("즉시 결과 반환")
                    return result  # 바로 결과를 반환하는 경우
                
                # 콜백 방식과 폴링 방식 모두 지원
                use_callback = True  # 콜백 방식 사용 여부
                
                if use_callback:
                    # 콜백 매니저를 통한 결과 대기
                    print(f"콜백 매니저를 통한 결과 대기: {execution_id}")
                    result = await callback_manager.wait_for_result(execution_id, timeout=30.0)
                    if result.get("status") == "timeout":
                        # 타임아웃 시 폴링으로 전환
                        print("콜백 타임아웃, 폴링으로 전환")
                        use_callback = False
                    else:
                        return result.get("result", {})
                
                if not use_callback:
                    # 폴링 방식으로 결과 대기 (기존 코드)
                    status_url = f"{base_url}/sse/status/{execution_id}"
                    print(f"상태 확인 URL: {status_url}")
                    
                    max_retries = 30
                    retry_count = 0
                    
                    while retry_count < max_retries:
                        status_response = await self.client.get(status_url)
                        
                        print(f"상태 확인 응답 코드: {status_response.status_code}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"상태 데이터: {status_data}")
                            
                            if status_data.get("status") == "completed":
                                return status_data.get("result", {})
                            elif status_data.get("status") == "error":
                                raise Exception(f"도구 실행 오류: {status_data.get('result', {}).get('error', '알 수 없는 오류')}")
                        
                        # 1초 대기 후 재시도
                        await asyncio.sleep(1)
                        retry_count += 1
                    
                    raise TimeoutError(f"도구 {tool_name} 실행 결과 대기 시간 초과")
            else:
                error_msg = f"서버 응답 오류: {response.status_code} - {response.text}"
                print(error_msg)
                raise Exception(error_msg)
        except Exception as e:
            print(f"도구 실행 오류: {str(e)}")
            raise Exception(f"도구 실행 오류: {str(e)}")
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """작업 상태 조회"""
        if not self.client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        
        # 모든 서버에 작업 상태 요청 (병렬)
        tasks = []
        for url in self.server_urls:
            tasks.append(self.client.get(f"{url}/task/{task_id}"))
        
        if not tasks:
            return {"task_id": task_id, "status": "unknown", "result": None}
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, httpx.Response) and result.status_code == 200:
                try:
                    return result.json()  # 첫 번째 성공 응답 반환
                except Exception:
                    continue
        
        return {"task_id": task_id, "status": "unknown", "result": None}
    
    
    