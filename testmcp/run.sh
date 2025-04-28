#!/bin/bash

# 현재 디렉토리 확인
echo "Working directory: $(pwd)"

# .env 파일 존재 확인
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create it first."
    exit 1
fi

# 필요한 디렉토리 생성
mkdir -p data
mkdir -p logs

echo "Setting up the environment..."

# 도커 네트워크 확인 및 생성
if ! docker network ls | grep -q "mcp_network"; then
    echo "Creating docker network: mcp_network"
    docker network create mcp_network
fi

# 이전 컨테이너 중지 (필요시)
# docker-compose down

# 도커 컴포즈 빌드 및 실행
echo "Building and starting services..."
docker-compose up -d --build

# 서비스 상태 확인
echo "Checking service status..."
sleep 5
docker-compose ps

echo "========================================"
echo "MCP Celery System is now running!"
echo "========================================"
echo "API Server: http://localhost:$(grep CLIENT_PORT .env | cut -d '=' -f2)"
echo "MCP Server: http://localhost:$(grep TOOL_PORT .env | cut -d '=' -f2)"
echo "========================================"
echo "Use 'docker-compose logs -f SERVICE_NAME' to view logs"
echo "SERVICE_NAME can be: api_server, mcp_server, celery_worker_math, redis"
echo "Use 'docker-compose down' to stop all services"
echo "========================================"