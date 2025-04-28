import redis
import json
import os
import asyncio
from typing import Dict, Any, Optional, Callable, List
import logging

logger = logging.getLogger(__name__)

class ToolCallbackManager:
    """도구 콜백 관리자 클래스"""
    
    _instance = None
    _callbacks = {}  # 콜백 이벤트 저장소: {execution_id: event}
    _results = {}    # 콜백 결과 저장소: {execution_id: result}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolCallbackManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """초기화"""
        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        
        try:
            self.redis_client = redis.Redis(
                host=self.redis_host, 
                port=self.redis_port, 
                db=0
            )
            logger.info("Redis 클라이언트 초기화 성공")
        except Exception as e:
            logger.error(f"Redis 클라이언트 초기화 실패: {str(e)}")
            self.redis_client = None
    
    async def register_callback(self, execution_id: str) -> asyncio.Event:
        """콜백 등록"""
        event = asyncio.Event()
        self._callbacks[execution_id] = event
        logger.info(f"콜백 등록: {execution_id}")
        return event
    
    def set_result(self, execution_id: str, result: Dict[str, Any]):
        """콜백 결과 설정"""
        self._results[execution_id] = result
        
        # 이벤트가 등록된 경우 설정
        if execution_id in self._callbacks:
            self._callbacks[execution_id].set()
            logger.info(f"콜백 이벤트 설정: {execution_id}")
    
    async def wait_for_result(self, execution_id: str, timeout: float = 30.0) -> Dict[str, Any]:
        """결과 대기"""
        if execution_id not in self._callbacks:
            event = await self.register_callback(execution_id)
        else:
            event = self._callbacks[execution_id]
        
        # 결과가 이미 있는 경우
        if execution_id in self._results:
            return self._results[execution_id]
        
        # 결과 대기
        try:
            await asyncio.wait_for(event.wait(), timeout)
            if execution_id in self._results:
                return self._results[execution_id]
            else:
                return {"status": "timeout", "error": "결과를 받지 못했습니다."}
        except asyncio.TimeoutError:
            return {"status": "timeout", "error": "대기 시간 초과"}
    
    def get_result(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """결과 반환 (동기 방식)"""
        return self._results.get(execution_id)
    
    def cleanup(self, execution_id: str):
        """리소스 정리"""
        if execution_id in self._callbacks:
            del self._callbacks[execution_id]
        if execution_id in self._results:
            del self._results[execution_id]
        
        # Redis에서도 정리
        if self.redis_client:
            try:
                self.redis_client.delete(f"callback:{execution_id}")
            except Exception as e:
                logger.error(f"Redis 정리 중 오류: {str(e)}")

# 싱글톤 인스턴스
callback_manager = ToolCallbackManager() 