from celery_workers.tasks.math_tasks import add, multiply, subtract, divide
import logging
import json

logger = logging.getLogger(__name__)

def execute(args):
    """수학 도구 실행 함수"""
    # 전체 args 내용 로깅
    logger.info(f"도구 실행 요청 전체 args: {json.dumps(args)}")
    
    # tool_name이 args 내부에 있을 수도 있음
    tool_name = args.get("tool_name", "")
    
    # args 내에 중첩된 정보가 있는지 확인
    if not tool_name and isinstance(args, dict) and "args" in args and isinstance(args["args"], dict):
        # 중첩된 args 내에서 tool_name 확인
        nested_args = args["args"]
        if "tool_name" in nested_args:
            tool_name = nested_args["tool_name"]
            logger.info(f"중첩된 args에서 tool_name 발견: {tool_name}")
            # args를 내부 args로 대체
            args = nested_args
    
    logger.info(f"최종 도구 이름: {tool_name}, 인자: {args}")
    
    # "a"와 "b" 값 확인
    a_value = args.get("a", None)
    b_value = args.get("b", None)
    
    if a_value is None or b_value is None:
        logger.error(f"필수 인자 a 또는 b가 없습니다: {args}")
        raise ValueError(f"도구 실행에 필요한 a, b 인자가 없습니다: {args}")
    
    result = None
    if tool_name == "add":
        result = add(args["a"], args["b"])
    elif tool_name == "multiply":
        result = multiply(args["a"], args["b"])
    elif tool_name == "subtract":
        result = subtract(args["a"], args["b"])
    elif tool_name == "divide":
        result = divide(args["a"], args["b"])
    elif not tool_name:
        logger.error(f"도구 이름이 지정되지 않았습니다. 시스템에 문제가 있습니다.")
        raise ValueError(f"도구 이름이 지정되지 않았습니다: {args}")
    else:
        raise ValueError(f"지원하지 않는 수학 도구: {tool_name}")
    
    logger.info(f"도구 실행 결과: {result}")
    return result