def search_docs_main(
    folder_names: list = None, 
    keywords: list = None,
    doc_type: str = None,
    search_in_content: bool = False
):
    """
    특정 폴더들 내에서 키워드와 조건을 기반으로 문서를 검색하는 함수
    
    :param folder_names: 검색할 폴더 이름 리스트 (예: ['MR24010002M', 'MR24010003M'])
    :param keywords: 검색할 키워드들 (파일 이름에 포함되어야 하는 단어들)
    :param doc_type: 문서 형식 (예: 'docx', 'xlsx', 'pdf')
    :param search_in_content: 파일 내용 검색 여부 (기본값: False)
    :return: 검색된 파일 정보의 리스트
    """
    
    import os
    import zipfile
    from datetime import datetime
    
    root_path = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\mcpclient\app\mockup_data"

    if not folder_names or not isinstance(folder_names, list):
        return {"status": "error", "message": "유효한 폴더 이름 리스트가 필요합니다."}
    
    result_files = []
    
    for folder_name in folder_names:
        folder_path = os.path.join(root_path, folder_name)
        
        # 폴더가 존재하지 않으면 다음 폴더로 넘어감
        if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
            print(f"폴더를 찾을 수 없음: {folder_path}")
            continue
        
        # 폴더 내 모든 파일 탐색 (하위 폴더 포함)
        for root, _, files in os.walk(folder_path):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                
                # ZIP 파일 처리
                if file_name.lower().endswith('.zip'):
                    try:
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            for zip_file_path in zip_ref.namelist():
                                if zip_file_path.endswith('/'):
                                    continue
                                
                                # 파일명 추출 (경로의 마지막 부분)
                                file_name_in_zip = os.path.basename(zip_file_path)
                                
                                if not file_name_in_zip:
                                    continue
                                
                                # 문서 타입 필터링
                                if doc_type and not file_name_in_zip.lower().endswith(f".{doc_type.lower()}"):
                                    continue
                                
                                # 키워드 필터링
                                if keywords and not all(keyword.lower() in file_name_in_zip.lower() for keyword in keywords):
                                    continue
                                
                                # 파일 정보 추출
                                zip_file_info = zip_ref.getinfo(zip_file_path)
                                
                                # 파일 정보 추가
                                zip_result_file = {
                                    "file_name": file_name_in_zip,
                                    "zip_path": file_path, # zip 경로 (예: "C:\폴더\MR24010002M\파일모음.zip")
                                    "path_in_zip": zip_file_path,  # zip 내부에서 파일 경로 (예: "문서/보고서.docx")
                                    "folder_name": folder_name,
                                    "file_type": file_name_in_zip.split('.')[-1] if '.' in file_name_in_zip else None,
                                    "in_zip": True,
                                }
                                
                                result_files.append(zip_result_file)
                                print("\nzip파일 추가")
                                print(f"키워드: {keywords}")
                                print(zip_result_file)
                    
                    except Exception as e:
                        print(f"ZIP 파일 {file_path} 처리 중 오류 발생: {str(e)}")
                
                # 일반 파일 처리
                else:
                    # 문서 타입 필터링
                    if doc_type and not file_name.lower().endswith(f".{doc_type.lower()}"):
                        continue
                    
                    # 키워드 필터링
                    if keywords and not all(keyword.lower() in file_name.lower() for keyword in keywords):
                        continue
                    
                    # 파일 정보 추가
                    file_info = {
                        "file_name": file_name,
                        "file_path": file_path,
                        "folder_name": folder_name,
                        "file_type": file_name.split('.')[-1] if '.' in file_name else None,
                        "in_zip": False
                    }
                    
                    # 파일 내용 검색 로직 ing
                    if search_in_content and keywords:
                        # 여기에 파일 내용 검색 로직을 추가할 수 있음
                        pass
                    
                    result_files.append(file_info)
                    print("\n파일 추가")
                    print(f"키워드: {keywords}")
                    print(file_info)
    
    if not result_files:
        return {"status": "info", "message": "검색 조건에 맞는 파일을 찾을 수 없습니다."}
    
    return result_files