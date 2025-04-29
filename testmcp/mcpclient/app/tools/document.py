from mcp.server.fastmcp import FastMCP

import markdown

def read_markdown_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
        # Parse markdown content to HTML
        html_content = markdown.markdown(content)
        return html_content
    except FileNotFoundError:
        print(f"Error: File not found at path: {file_path}")
        return None
    except Exception as e:
        print(f"Error reading file: {e}")
        return None

mcp = FastMCP("document")

@mcp.tool()
def read_header(file_path:str):
    """
    Read the first 5 lines of a markdown file.
    """
    text = read_markdown_file(file_path).split("\n")
    n_lines = len(text)
    return text[0:max(int(n_lines/10), 5)]

@mcp.tool()
def read_body(file_path:str):
    """
    Read the body of a markdown file.
    """
    text = read_markdown_file(file_path).split("\n")
    n_lines = len(text)
    return text[max(int(n_lines/10), 5):]




if __name__ == "__main__":
    mcp.run(transport='stdio')