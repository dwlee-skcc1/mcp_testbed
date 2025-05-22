# import os

# def find_docx_files(root_path):
#     """
#     지정된 경로와 모든 하위 폴더에서 docx 파일을 찾아 이름을 출력합니다.
    
#     :param root_path: 검색을 시작할 루트 경로
#     """
#     # 파일 카운터 초기화
#     docx_count = 0
    
#     # 폴더를 재귀적으로 탐색
#     for root, _, files in os.walk(root_path):
#         for file_name in files:
#             # docx 파일인지 확인
#             if file_name.lower().endswith('.docx'):
#                 docx_count += 1
#                 # 파일 이름만 출력
#                 print(f"{docx_count}. {file_name}")
#                 # 전체 경로도 보고 싶다면 아래 주석을 해제하세요
#                 # print(f"{docx_count}. {file_name} (경로: {os.path.join(root, file_name)})")
    
#     # 검색 결과 요약
#     if docx_count == 0:
#         print("docx 파일을 찾지 못했습니다.")
#     else:
#         print(f"\n총 {docx_count}개의 docx 파일을 찾았습니다.")

# # 검색 경로 설정
# search_path = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\mcpclient\app\data_test"
# # 함수 실행
# print(f"'{search_path}' 폴더에서 docx 파일 검색 중...\n")
# find_docx_files(search_path)


import os

def explore_directory(path):
    print(f"탐색 시작: {path}\n")
    
    # 파일 카운트를 위한 변수
    file_count = 0
    
    # 이미 처리한 파일 경로를 저장하는 집합(중복 확인용)
    processed_files = set()
    
    # 모든 디렉토리와 파일 탐색
    for root, _, files in os.walk(path):
        for file_name in files:
            print(file_name)
            file_path = os.path.join(root, file_name)
            file_count += 1
            
            # 중복 체크
            is_duplicate = file_path in processed_files
            processed_files.add(file_path)
            
            # print(f"  파일 {file_count}: {file_path} {'(중복)' if is_duplicate else ''}")
    
    print(f"\n총 처리된 파일 수: {file_count}")
    print(f"고유 파일 수: {len(processed_files)}")
    if file_count > len(processed_files):
        print(f"중복 처리된 파일 수: {file_count - len(processed_files)}")

# 지정된 경로 탐색
path = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\mcpclient\app\data_test"
explore_directory(path)