from fastapi import FastAPI
import uvicorn, os
from pathlib import Path
from dotenv import load_dotenv

from router import sample_api, document_api

app = FastAPI()

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
if not ENV_FILE.exists():
    ENV_FILE = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

client_port = int(os.getenv("CLIENT_PORT"))
tool_port = int(os.getenv("TOOL_PORT"))


app.include_router(sample_api.router, prefix="/sample", tags=["sample"])
app.include_router(document_api.router, prefix="/document", tags=["document"])

@app.get("/")
def home():
    return {"message": "Hello World"}

    
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=client_port)
