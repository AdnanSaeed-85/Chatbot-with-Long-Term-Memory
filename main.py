from fastmcp import FastMCP

mcp = FastMCP('mcp')

@mcp.tool
def addition(x, y):
    "you will received 2 numbers, you have to perform summition and return a single digit"
    return x + y

@mcp.tool
def subtraction(x, y):
    "you will received 2 numbers, you have to perform subtraction and return a single digit answer"
    return x - y

@mcp.tool
def rag_system(query: str):
    # Indexing
    # Embeddings
    # Retrieval
    # Generation
    pass

if __name__ == '__main__':
    mcp.run()