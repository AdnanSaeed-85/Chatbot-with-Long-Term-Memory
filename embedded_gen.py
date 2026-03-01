from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from CONFIG import PDFS, INDEX_PATH, EMBED_MODEL
from typing import List

load_dotenv()

def generate_embeddings(PDFS: List[str], INDEX_PATH: str, EMBED_MODEL: str):
    docs = []
    for path in PDFS:
        docs.extend(PyPDFLoader(path).load())

    text_splitting = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=120).split_documents(docs)

    embed_model = OpenAIEmbeddings(model=EMBED_MODEL)
    embeddings = FAISS.from_documents(text_splitting, embed_model)

    embeddings.save_local(INDEX_PATH)
    print("✅ FAISS index saved")


generate_embeddings(PDFS, INDEX_PATH, EMBED_MODEL)