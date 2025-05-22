import os
import pandas as pd
from pathlib import Path
from docx import Document

# 파일 및 폴더 경로
base_path = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\mcpclient\app\mockup_data"
excel_file = os.path.join(base_path, "RDB.xlsx")

# Excel 파일 읽기
try:
    # Excel 파일 로드
    df = pd.read_excel(excel_file)
    
    # MNRO와 제목 칼럼이 존재하는지 확인
    required_columns = ['MNRO', '제목']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        print(f"다음 칼럼이 존재하지 않습니다: {', '.join(missing_columns)}")
        exit(1)
    
    # 데이터프레임을 MNRO 별로 그룹화
    grouped = df.groupby('MNRO')
    
    # 각 MNRO에 대해 폴더 생성 및 워드 파일 생성
    for mnro, group in grouped:
        # MNRO 값이 유효한지 확인
        if pd.isna(mnro) or str(mnro).strip() == '':
            continue
            
        # 폴더명으로 사용할 MNRO 값
        folder_name = str(mnro).strip()
        folder_path = os.path.join(base_path, folder_name)
        
        # 폴더 생성
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
            print(f"폴더 생성 완료: {folder_path}")
        else:
            print(f"폴더가 이미 존재합니다: {folder_path}")
        
        # 해당 MNRO의 모든 제목에 대해 워드 파일 생성
        for _, row in group.iterrows():
            title = row['제목']
            
            # 제목이 유효한지 확인
            if pd.isna(title) or str(title).strip() == '':
                continue
                
            # 파일명으로 사용할 제목 (파일명에 사용할 수 없는 문자 처리)
            file_name = str(title).strip()
            # 파일명에 사용할 수 없는 문자 처리
            invalid_chars = ['\\', '/', ':', '*', '?', '"', '<', '>', '|']
            for char in invalid_chars:
                file_name = file_name.replace(char, '_')
                
            # 워드 파일 경로
            file_path = os.path.join(folder_path, f"{file_name}.docx")
            
            # 이미 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                # 빈 워드 문서 생성
                doc = Document()
                doc.save(file_path)
                print(f"워드 파일 생성 완료: {file_path}")
            else:
                print(f"워드 파일이 이미 존재합니다: {file_path}")
    
    print("모든 폴더 및 파일 생성이 완료되었습니다.")
    
except Exception as e:
    print(f"오류 발생: {e}")