# """
# KaravanTech MCP Server
# ----------------------
# Features:
# 1. Offline FAISS index builder
# 2. Persistent RAG tool
# 3. Math tools
# 4. Agent-ready MCP server
# """

# import os
# from dotenv import load_dotenv
# from fastmcp import FastMCP

# from langchain_openai import ChatOpenAI, OpenAIEmbeddings
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS

# load_dotenv()

# # ================================
# # CONFIG
# # ================================

# PDFS = [
#     r"A:\PRO\p1\KaravanTech_Company_Policies.pdf",
#     r"A:\PRO\p1\KaravanTech_Company_Profile.pdf",
#     r"A:\PRO\p1\KaravanTech_Products_and_Pricing.pdf",
# ]

# INDEX_PATH = "karavantech_faiss"

# EMBED_MODEL = "text-embedding-3-small"
# CHAT_MODEL = "gpt-4o-mini"

# # ================================
# # MCP SERVER
# # ================================

# mcp = FastMCP("karavan_mcp")

# # ================================
# # OFFLINE INDEX BUILDER
# # Run once: python main.py build
# # ================================

# def build_index():
#     print("📚 Loading PDFs...")
#     docs = []
#     for path in PDFS:
#         if not os.path.exists(path):
#             print(f"⚠ Missing file: {path}")
#             continue
#         docs.extend(PyPDFLoader(path).load())

#     splitter = RecursiveCharacterTextSplitter(
#         chunk_size=500,
#         chunk_overlap=120,
#     )

#     chunks = splitter.split_documents(docs)

#     print(f"📄 Total chunks: {len(chunks)}")

#     embed = OpenAIEmbeddings(model=EMBED_MODEL)
#     vectordb = FAISS.from_documents(chunks, embed)

#     vectordb.save_local(INDEX_PATH)
#     print("✅ FAISS index saved")


# # ================================
# # LOAD VECTOR DB (ON SERVER START)
# # ================================

# def load_vector_db():
#     if not os.path.exists(INDEX_PATH):
#         raise RuntimeError(
#             "FAISS index not found. Run: python main.py build"
#         )

#     embed = OpenAIEmbeddings(model=EMBED_MODEL)
#     vectordb = FAISS.load_local(
#         INDEX_PATH,
#         embed,
#         allow_dangerous_deserialization=True,
#     )
#     return vectordb.as_retriever(search_kwargs={"k": 4})


# retriever = None
# llm = ChatOpenAI(model=CHAT_MODEL)

# # ================================
# # MCP TOOLS
# # ================================

# @mcp.tool
# def addition(x: int, y: int) -> int:
#     """Add two integers."""
#     return x + y


# @mcp.tool
# def subtraction(x: int, y: int) -> int:
#     """Subtract two integers."""
#     return x - y


# @mcp.tool
# def karavan_rag(query: str) -> str:
#     """
#     Answer questions about KaravanTech company documents.
#     Uses company policies, profile, and product files.
#     """

#     global retriever
#     if retriever is None:
#         retriever = load_vector_db()

#     docs = retriever.invoke(query)

#     if not docs:
#         return "No relevant information found in company documents."

#     context = "\n\n".join(d.page_content for d in docs)

#     prompt = f"""
# You are a professional KaravanTech company assistant.

# Rules:
# - Answer ONLY using provided context.
# - If answer not in context, say: "Not found in company documents."

# Context:
# {context}

# Question:
# {query}
# """

#     response = llm.invoke(prompt)
#     return response.content


# # ================================
# # MAIN
# # ================================

# if __name__ == "__main__":
#     import sys

#     if len(sys.argv) > 1 and sys.argv[1] == "build":
#         build_index()
#     else:
#         print("🚀 Starting MCP server...")
#         print("👉 Run 'python main.py build' first if index not created")
#         mcp.run()