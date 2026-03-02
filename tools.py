from fastmcp import FastMCP
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from CONFIG import EMBED_MODEL
from langchain_core.tools import tool
from langgraph.types import interrupt

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
        
                  **HUMAN-IN-THE-LOOP**
    before give any information about KaravanTech, this tool will interrupt
    and wait for human decision (yes/ anything else)
    """
    retrieved = retriever.invoke(query)
    docs = "\n\n".join(ret.page_content for ret in retrieved)

    human_decision = interrupt("Type yes to allow, anything else to deny")
    if human_decision.strip().lower() != "yes":
        return "Denied by human."

    return docs

@mcp.tool
def addition(x, y):
    'add x and y'
    return x + y

if __name__ == "__main__":
    mcp.run(
        transport="sse",
        host="0.0.0.0",
        port=8000
    )