from fastmcp import FastMCP

mcp = FastMCP('MCP_Server')

@mcp.tool
def subtraction(x, y):
    'add x and y'
    return x + y

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8000
    )