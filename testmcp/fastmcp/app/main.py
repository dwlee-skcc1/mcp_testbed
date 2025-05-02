from mcp.server.fastmcp import FastMCP
from fastmcp.prompts.base import UserMessage
from mcp.types import TextContent
from langchain_openai import AzureChatOpenAI

import os
import logging
import psycopg2
from psycopg2 import Error
import re
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로딩 - 프로그램 시작 시 한 번만 수행
ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_FILE, override=True)

# Configure logging
log_dir = r"C:\Users\Administrator\Desktop\ye\LKM\Tools\mcp_testbed\testmcp\fastmcp\app\logs"
os.makedirs(log_dir, exist_ok=True) 
log_file = os.path.join(log_dir, "rdb_search.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, mode='a', encoding='utf-8'),  # 파일에 추가(append)
        logging.StreamHandler()  # 콘솔에도 출력
    ]
)
logger = logging.getLogger("rdb_search_tool")

# PostgreSQL 연결 설정 - 전역 변수로 한 번만 설정
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": os.getenv("DB_PORT", 5432)
}

# Azure OpenAI 설정 (전역으로 한 번만 설정)
def create_llm():
    return AzureChatOpenAI(
        azure_deployment=os.getenv("OPENAI_DEPLOYMENT"),
        azure_endpoint=os.getenv("OPENAI_ENDPOINT"),
        api_version=os.getenv("OPENAI_API_VERSION"),
        api_key=os.getenv("OPENAI_API_KEY"),
        n=1,
        temperature=0,
        max_tokens=500,
        model=os.getenv("OPENAI_MODEL"),
        verbose=True,
        streaming=False,
    )



mcp = FastMCP("test")

@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

@mcp.tool()
def multiply(a: int, b: int) -> int:
    """Multiply two numbers"""
    return a * b



def extract_sql_from_response(content):
    """Extract SQL query from LLM response."""
    # Look for SQL between code blocks
    sql_pattern = r"```sql\s*(.*?)\s*```"
    matches = re.findall(sql_pattern, content, re.DOTALL)
    
    if matches:
        return matches[0].strip()
    else:
        # Fallback to try finding SQL without explicit markers
        # This is less reliable but helps in case formatting is inconsistent
        try:
            # 일반적인 SQL 패턴을 찾되, 주석은 제외
            sql_keywords = r"(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)"
            matches = re.findall(f"{sql_keywords}.*?;", content, re.DOTALL | re.IGNORECASE)
            if matches:
                return matches[0].strip()
        except Exception as e:
            logger.error(f"Error in SQL extraction fallback: {str(e)}")
        
    return None

def get_db_schema(conn):
    """Get database schema for the connected PostgreSQL database."""
    schema = []
    
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                set search_path to ocean_h;
                show search_path;
                           """)
            
            # Get list of tables
            cursor.execute("""
                SELECT table_schema,table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'ocean_h'
            """)
            tables = cursor.fetchall()
            
            if not tables:
                logger.warning("No tables found in the database")
                return "No tables found in the database schema."
                
            for table in tables:
                table_schema = table[0]
                table_name = table[1]
                
                # Get column information for each table
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table_name}'
                """)
                columns = cursor.fetchall()
                
                table_info = f"Table: {table_schema}.{table_name}\nColumns:\n"
                for col in columns:
                    col_name, col_type = col
                    table_info += f"  - {col_name}: {col_type}\n"
                
                # 추가: 기본 키 정보 가져오기
                cursor.execute(f"""
                    SELECT c.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.constraint_column_usage AS ccu USING (constraint_schema, constraint_name)
                    JOIN information_schema.columns AS c ON c.table_schema = tc.constraint_schema
                      AND tc.table_name = c.table_name AND ccu.column_name = c.column_name
                    WHERE constraint_type = 'PRIMARY KEY' AND tc.table_name = '{table_name}'
                """)
                pks = cursor.fetchall()
                if pks:
                    pk_names = [pk[0] for pk in pks]
                    table_info += f"Primary Key(s): {', '.join(pk_names)}\n"
                
                schema.append(table_info)
            
            cursor.execute("""
                set search_path to default;
                           """)
        
        
        return "\n".join(schema)
    
    except Error as e:
        logger.error(f"Error retrieving database schema: {str(e)}")
        return f"Error retrieving schema: {str(e)}"

def fix_sql_query(llm, db_schema, query, sql_query, error_info):
    """Fix SQL syntax errors using the LLM."""
    
    system_prompt = f"""You are a PostgreSQL database expert. Review the user's question, 
    the database schema, the SQL query that was generated, and the error message returned by 
    the database. Fix ONLY the syntax errors in the SQL query without changing the logic.
    Output ONLY the fixed SQL query wrapped in ```sql and ``` tags.

    Database Schema:
    {db_schema}
    """

    user_prompt = f"""Question: {query}

    SQL Query with errors:
    {sql_query}

    Error message:
    {error_info}

    Please fix the SQL syntax errors only. Return ONLY the corrected SQL query."""

    messages = [
        UserMessage(content=user_prompt),
    ]
    
    try:
        response = llm.invoke(system_prompt + "\n\n" + user_prompt)
        content = response.content
        fixed_sql = extract_sql_from_response(content)
        
        if fixed_sql:
            logger.info(f"SQL query fixed: {fixed_sql}")
            return fixed_sql
        else:
            logger.warning("Failed to extract fixed SQL from LLM response")
            return sql_query  # Return original if extraction failed
    except Exception as e:
        logger.error(f"Error in fix_sql_query: {str(e)}")
        return sql_query

@mcp.tool()
def search_rdb(query: str) -> list[TextContent]:
    """
    Search the relational database using natural language query.
    
    Args:
        query: Natural language query to search the database
    """
    logger.info(f"Processing RDB search query: {query}")
    
    # Create LLM instance
    try:
        llm = create_llm()
    except Exception as e:
        error_msg = f"Failed to initialize LLM: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    conn = None
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(**DB_CONFIG)
        
        # Get database schema for prompt context
        db_schema = get_db_schema(conn)
        logger.info(f"Database schema retrieved successfully:\n{db_schema}")
        print('\ndb_schema')
        print(db_schema)
      
        
        # Generate SQL from natural language query
        system_prompt = f"""You are a PostgreSQL database expert. Your task is to convert natural language questions
        into correct SQL queries based on the database schema provided. Return ONLY the SQL query wrapped in 
        ```sql and ``` tags. Ensure the SQL is syntactically correct for PostgreSQL.

        Database Schema:
        {db_schema}
        """

        user_prompt = f"Convert this question to SQL: {query}"
        
        # Call LLM to generate SQL
        logger.info("Calling LLM to generate SQL query")
        response = llm.invoke(system_prompt + "\n\n" + user_prompt)
        content = response.content
        sql_query = extract_sql_from_response(content)
        
        logger.info(f"Generated SQL query: {sql_query}")
        print('\nsql_query')
        print(sql_query)
        
        if not sql_query:
            return [TextContent(type="text", text="Failed to generate SQL query from the question. Please try rephrasing your question.")]
        
        # Execute the SQL query
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql_query)
                
                # Check if there are results (might be an INSERT, UPDATE, etc.)
                if cursor.description is None:
                    affected_rows = cursor.rowcount
                    conn.commit()  # 필요한 경우 변경사항을 커밋
                    return [TextContent(type="text", text=f"SQL Query:\n```sql\n{sql_query}\n```\n\nQuery executed successfully. Affected rows: {affected_rows}")]
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                # Format the results as markdown table
                result_md = "| " + " | ".join(columns) + " |\n"
                result_md += "| " + " | ".join(["---" for _ in columns]) + " |\n"
                
                if not rows:
                    result_md += "| No results found |" + " | ".join(["" for _ in range(len(columns)-1)]) + " |\n"
                else:
                    for row in rows[:100]:  # Limit to 100 rows
                        row_values = [str(val) if val is not None else "NULL" for val in row]
                        result_md += "| " + " | ".join(row_values) + " |\n"
                    
                    if len(rows) > 100:
                        result_md += "\n_Note: Results limited to 100 rows._"
                
                return [TextContent(type="text", text=f"SQL Query:\n```sql\n{sql_query}\n```\n\nResults:\n{result_md}")]
                
        except Error as e:
            # Try to fix SQL if there's an error
            logger.error(f"SQL execution error: {str(e)}")
            
            for attempt in range(3):
                logger.info(f"SQL error occurred, attempting fix #{attempt+1}")
                fixed_sql = fix_sql_query(llm, db_schema, query, sql_query, str(e))
                
                if fixed_sql == sql_query:
                    logger.warning("No changes made to SQL query after fix attempt")
                    break  # Break if no changes were made
                    
                logger.info(f"SQL query modified: {fixed_sql}")
                sql_query = fixed_sql
                print('\nfixed_sql_query')
                print(sql_query)
                
                try:
                    with conn.cursor() as cursor:
                        cursor.execute(sql_query)
                        
                        # Check if there are results (might be an INSERT, UPDATE, etc.)
                        if cursor.description is None:
                            affected_rows = cursor.rowcount
                            conn.commit()  # 필요한 경우 변경사항을 커밋
                            return [TextContent(type="text", text=f"SQL Query (fixed):\n```sql\n{sql_query}\n```\n\nQuery executed successfully. Affected rows: {affected_rows}")]
                        
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()
                        
                        # Format the results as markdown table
                        result_md = "| " + " | ".join(columns) + " |\n"
                        result_md += "| " + " | ".join(["---" for _ in columns]) + " |\n"
                        
                        if not rows:
                            result_md += "| No results found |" + " | ".join(["" for _ in range(len(columns)-1)]) + " |\n"
                        else:
                            for row in rows[:100]:  # Limit to 100 rows
                                row_values = [str(val) if val is not None else "NULL" for val in row]
                                result_md += "| " + " | ".join(row_values) + " |\n"
                            
                            if len(rows) > 100:
                                result_md += "\n_Note: Results limited to 100 rows._"
                        
                        return [TextContent(type="text", text=f"SQL Query (fixed):\n```sql\n{sql_query}\n```\n\nResults:\n{result_md}")]
                        
                except Error as e2:
                    logger.error(f"Error after fix attempt #{attempt+1}: {str(e2)}")
                    if attempt == 2:  # Last attempt
                        return [TextContent(type="text", text=f"Failed to execute SQL query after multiple fix attempts.\n\nSQL Query:\n```sql\n{sql_query}\n```\n\nError: {str(e2)}\n\nPlease try rephrasing your question or check if the requested data exists in the database.")]
    
    except Error as e:
        error_msg = f"Database connection error: {str(e)}"
        logger.error(error_msg)
        return [TextContent(type="text", text=error_msg)]
    
    finally:
        if conn:
            conn.close()
            logger.info("Database connection closed")


    








if __name__ == "__main__":
    mcp.run(transport='sse')