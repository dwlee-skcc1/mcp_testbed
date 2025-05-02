import pandas as pd
import psycopg2
from sqlalchemy import create_engine
from pathlib import Path

def excel_to_postgresql(excel_path, db_name='rdb_database', table_name='rdb_table', 
                        host='localhost', port='5432', user='postgres', password='your_password'):
    """
    Excel 파일을 PostgreSQL 관계형 데이터베이스로 변환합니다.
    
    Args:
        excel_path (str): Excel 파일 경로
        db_name (str): 생성할 PostgreSQL 데이터베이스 이름
        table_name (str): 생성할 테이블 이름
        host (str): PostgreSQL 호스트
        port (str): PostgreSQL 포트
        user (str): PostgreSQL 사용자 이름
        password (str): PostgreSQL 패스워드
    
    Returns:
        bool: 성공 여부
    """
    # Excel 파일 읽기
    try:
        excel_data = pd.read_excel(excel_path)
        print(f"엑셀 파일 로드 성공. 열: {excel_data.columns.tolist()}")
        print(f"데이터 샘플:\n{excel_data.head()}")
    except Exception as e:
        print(f"엑셀 파일 로딩 오류: {e}")
        return False
    
    # PostgreSQL 연결 
    try:
        # 먼저 PostgreSQL 서버에 연결
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 기존 데이터베이스가 있는지 확인하고 없으면 생성
        cursor.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        if not exists:
            print(f"데이터베이스 {db_name} 생성 중...")
            cursor.execute(f"CREATE DATABASE {db_name}")
        
        conn.close()
        
        # SQLAlchemy 엔진 생성 및 데이터 삽입
        engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db_name}')
        
        # 엑셀 데이터를 PostgreSQL 테이블로 저장
        excel_data.to_sql(table_name, engine, if_exists='replace', index=False)
        
        # 데이터 확인
        with engine.connect() as connection:
            result = connection.execute(f"SELECT * FROM {table_name} LIMIT 5")
            print("데이터베이스 생성 성공. 샘플 데이터:")
            for row in result:
                print(row)
                
        print(f"PostgreSQL 데이터베이스 {db_name}에 {table_name} 테이블이 생성되었습니다.")
        return True
        
    except Exception as e:
        print(f"PostgreSQL 데이터베이스 생성 오류: {e}")
        import traceback
        print(traceback.format_exc())
        return False

# 사용 예시
if __name__ == "__main__":
    excel_path = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\mcpclient\app\mockup_data\RDB.xlsx"
    
    # PostgreSQL 연결 정보 수정 필요
    success = excel_to_postgresql(
        excel_path=excel_path,
        db_name='rdb_database',
        table_name='rdb_table',
        host='localhost',
        port='5432',
        user='postgres',
        password='your_password'  # 실제 비밀번호로 변경 필요
    )
    
    if success:
        print("PostgreSQL 변환 완료")
    else:
        print("PostgreSQL 변환 실패")