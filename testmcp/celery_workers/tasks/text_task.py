"""텍스트 처리 도구 모듈"""

def execute(args):
    """텍스트 도구 실행 함수"""
    operation = args.get("operation", "")
    text = args.get("text", "")
    
    if operation == "uppercase":
        return {"result": text.upper()}
    elif operation == "lowercase":
        return {"result": text.lower()}
    else:
        return {"error": f"Unknown operation: {operation}"}