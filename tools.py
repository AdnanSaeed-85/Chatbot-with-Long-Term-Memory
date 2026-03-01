from fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from CONFIG import EMBED_MODEL
from langchain_core.tools import tool

load_dotenv()
mcp = FastMCP('MCP_Server')

def embedd_loading(embed_model_name: str):
    embedd_model = OpenAIEmbeddings(model=embed_model_name)
    embedd = FAISS.load_local('A:\\PRO\\p1\\karavantech_faiss', embedd_model, allow_dangerous_deserialization=True)
    retriever = embedd.as_retriever(search_type='similarity', search_kwargs={'k': 3})
    return retriever

retriever = embedd_loading(EMBED_MODEL)

@tool
def karavan_rag(query: str) -> str:
    """
    Answer questions about KaravanTech company documents.
    Uses company policies, profile, and product files.
    """
    retrieved = retriever.invoke(query)
    return "\n\n".join(ret.page_content for ret in retrieved)

@mcp.tool
def addition(x, y):
    'add x and y'
    return x + y

if __name__ == '__main__':
    mcp.run()