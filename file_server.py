from mcp.server.fastmcp import FastMCP
import os

# Create a simple File Reader MCP Server
mcp = FastMCP("File Server")

@mcp.tool()
def read_file(filepath: str) -> str:
    """
    Reads the contents of a local file.
    Args:
        filepath: The absolute or relative path to the file.
    """
    try:
        if not os.path.exists(filepath):
            return f"Error: File '{filepath}' does not exist."
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Return truncated content if it's too large to save tokens
        max_chars = 5000
        if len(content) > max_chars:
            return content[:max_chars] + f"\n\n...[File truncated. Total length: {len(content)} characters]..."
        
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

if __name__ == "__main__":
    # Start the server using stdio transport
    mcp.run()
