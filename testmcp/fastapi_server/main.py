from fastapi import FastAPI, Depends
import uvicorn
import os
from pathlib import Path
from dotenv import load_dotenv

from fastapi_server.routers import sample_api

# 환경 변수 로드
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_FILE, override=True)

# 포트 설정
client_port = int(os.getenv("CLIENT_PORT", 8000))

# FastAPI 앱 생성
app = FastAPI(
    title="FastAPI Server",
    description="FastAPI Server with Langchain Agent Integration",
    version="0.1.0"
)

# # CORS 설정 (필요시)
# from fastapi.middleware.cors import CORSMiddleware
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # 프로덕션에서는 특정 출처만 허용하도록 변경 권장
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# 라우터 등록
app.include_router(sample_api.router, prefix="/sample", tags=["sample"])

# 홈 라우트
@app.get("/")
async def home():
    """API 서버 루트 엔드포인트"""
    return {
        "message": "FastAPI Server is running",
        "docs_url": "/docs",
        "version": "0.1.0"
    }

# 서버 실행 코드
if __name__ == "__main__":
    uvicorn.run("fastapi_server.main:app", host="0.0.0.0", port=client_port, reload=True)