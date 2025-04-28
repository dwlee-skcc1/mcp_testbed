# MCP Celery System

MCP(Model-Controller-Processor) 서버와 Celery Worker를 통합한 분산 처리 시스템입니다.

## 아키텍처

시스템은 다음과 같은 주요 컴포넌트로 구성됩니다:

1. **API 서버**: FastAPI를 기반으로 한 클라이언트 요청 처리 서버
2. **MCP 서버**: 도구(Tool) 관리 및 실행 요청을 Celery에 전달
3. **Celery 워커**: 각 도구의 실제 작업을 실행
4. **Redis**: Message Broker 및 Result Backend 역할

## 설치 및 실행

### 요구사항

- Docker 및 Docker Compose
- Python 3.9 이상 (로컬 개발 시)

### 실행 방법

1. `.env` 파일 설정

   ```
   # API 키 등 필요한 환경 변수 설정
   ```

2. 시스템 실행

   ```bash
   ./run.sh
   ```

3. 서비스 접근
   - API 서버: http://localhost:8000
   - MCP 서버: http://localhost:8001
   - API 문서: http://localhost:8000/docs

## 주요 기능

- LLM 에이전트를 통한 도구 실행 요청
- 도구 실행 작업의 비동기 처리
- 다양한 도구 타입 지원 (수학 연산, 파일 병합 등)
- 확장 가능한 구조로 새로운 도구 쉽게 추가 가능

## 도구 추가 방법

1. `mcp_server/tools/` 디렉토리에 새 도구 파일 생성
2. `@ToolDecorator` 데코레이터를 사용하여 도구 정의
3. `celery_workers/tasks/` 디렉토리에 해당 도구의 Celery 태스크 구현
4. `celery_workers/tools/tools.json` 파일에 도구 설정 추가
5. 필요시 새 워커 타입 추가 (`docker-compose.yml` 수정)

## 개발자 문서

자세한 내용은 [개발자 문서](docs/)를 참조하세요.