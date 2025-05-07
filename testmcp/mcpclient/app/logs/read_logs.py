import json
import os

def read_log_file(filename):
    log_dir = os.path.join('mcpclient', 'app', 'logs')
    log_path = os.path.join(log_dir, filename)
    
    with open(log_path, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def read_latest_log():
    log_dir = os.path.join("testmcp",'mcpclient', 'app', 'logs')
    
    # Get list of log files
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.json')]
    
    if not log_files:
        return None
        
    # Sort files by modification time and verify file exists
    latest_file = None
    try:
        latest_file = max(log_files, key=lambda x: os.path.getmtime(os.path.join(log_dir, x)))
        if not os.path.exists(os.path.join(log_dir, latest_file)):
            return None
    except (ValueError, FileNotFoundError):
        return None
    
    return read_log_file(latest_file)

# read_log_file("D:\dev\mcp_testbed\testmcp\mcpclient\app\logs\reponse_250507100005.json")
file_path =os.path.join("D:", "dev", "mcp_testbed", "testmcp", "mcpclient", "app", "logs", "reponse_250507100005.json")
read_log_file(file_path)





