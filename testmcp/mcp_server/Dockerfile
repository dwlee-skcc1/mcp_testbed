FROM python:3.10-slim

WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    libc-dev \
    && rm -rf /var/lib/apt/lists/*

# 필요한 파일 복사
COPY mcp_server /app/mcp_server
COPY requirements.txt /app/

# 패키지 설치
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# 환경 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app

# 서버 실행
CMD ["python", "-m", "mcp_server.server"]