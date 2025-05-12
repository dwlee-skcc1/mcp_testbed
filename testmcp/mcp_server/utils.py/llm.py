from langchain_openai import AzureChatOpenAI
from dotenv import load_dotenv
import os
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage


load_dotenv()

class LLMSingleton:
     _instance: Optional['LLMSingleton'] = None
     _llm: Optional[AzureChatOpenAI] = None
     
     def __new__(cls):
          if cls._instance is None:
               cls._instance = super(LLMSingleton, cls).__new__(cls)
               cls._instance._init_llm()
          return cls._instance
     
     def _init_llm(self):
          self._llm = AzureChatOpenAI(
               azure_deployment=os.getenv("OPENAI_DEPLOYMENT"),
               azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
               api_version=os.getenv("OPENAI_API_VERSION"),
               api_key=os.getenv("OPENAI_API_KEY"),
               n=1,
               temperature=0,
               max_tokens=None,
               model=os.getenv("OPENAI_MODEL"),
               verbose=True,
               streaming=True,
          )
     
     @classmethod
     def get_llm(cls) -> AzureChatOpenAI:
          if cls._instance is None:
               cls()
          return cls._instance._llm
     
     @classmethod
     def invoke_example(cls, message: str) -> AzureChatOpenAI:
          
          messages = [
               SystemMessage(content="너는 친절한 한국어 비서야."),
               HumanMessage(content=message)
          ]
          llm = cls.get_llm()
          return llm.invoke(messages)

# 기존 코드와의 호환성을 위해 llm 변수 유지
llm = LLMSingleton.get_llm()

