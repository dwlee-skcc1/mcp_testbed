import os
from dotenv import load_dotenv
from pathlib import Path


ENV_FILE = Path(__file__).resolve().parent.parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

from langchain_openai import AzureChatOpenAI

def get_model():
    model = AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        api_key=os.getenv("OPENAI_API_KEY"),
        n=1,
        temperature=0,
        max_tokens=4000,
        model=os.getenv("OPENAI_MODEL"),
        verbose=True,
        streaming=False,
        )
    return model