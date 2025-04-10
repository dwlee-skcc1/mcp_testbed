from langchain_mcp_adapters.client import MultiServerMCPClient

from fastapi import FastAPI
import uvicorn, os
from pathlib import Path
from dotenv import load_dotenv

from router.service import router

app = FastAPI()

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if not ENV_FILE.exists():
    ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))


app.include_router(router, prefix="/service")

@app.get("/")
def home():
    return {"message": "Hello World"}

@app.get("/connect_sse")
async def connect_sse():
    async with MultiServerMCPClient(
        {
        "test":{
            "url" : "http://127.0.0.1:%d/sse"%tool_port,
            "transport": "sse"
            }
        }
    ) as client:
        await client.__aenter__()
        tools = client.get_tools()
        return {"tools":str(tools)}
    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=client_port)
