from mcp.server.fastmcp import FastMCP

# Create a simple Math MCP Server
mcp = FastMCP("Math Server")

@mcp.tool()
def calculate(expression: str) -> str:
    """
    Evaluates a simple math expression.
    Supported operators: +, -, *, /
    Example: '5 * 10' or '100 / 4'
    """
    try:
        # We use a safe eval restricted to basic math
        allowed_chars = set("0123456789+-*/. ()")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression. Only numbers and basic math operators are allowed."
        
        # safely evaluate the math expression
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {str(e)}"

if __name__ == "__main__":
    # Start the server using stdio transport (the standard for MCP)
    mcp.run()
