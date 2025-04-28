import os
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

from langchain_openai import AzureChatOpenAI

def get_model():
    """Azure OpenAI 모델 인스턴스 반환"""
    # 환경 변수 가져오기
    azure_endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    api_version = os.getenv("OPENAI_API_VERSION")
    deployment = os.getenv("OPENAI_DEPLOYMENT")
    model_name = os.getenv("OPENAI_MODEL")
    
    # 필수 환경 변수 확인
    if not all([azure_endpoint, api_key, deployment]):
        raise ValueError("Required Azure OpenAI environment variables are missing.")
    
    # 모델 인스턴스 생성
    model = AzureChatOpenAI(
        azure_deployment=deployment,
        azure_endpoint=azure_endpoint,
        api_version=api_version or "2023-05-15",
        api_key=api_key,
        n=1,
        temperature=0,
        max_tokens=500,
        model=model_name,  # 일부 구성에서는 필요할 수 있음
        verbose=True,
        streaming=False,
    )
    return model