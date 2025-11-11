# retriever.py
import os
from dotenv import load_dotenv
import chromadb
from chromadb.config import Settings
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

chroma_client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="chroma_db"
))

collection = chroma_client.get_or_create_collection("docs")

def embed(text: str):
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding

def retrieve(query: str, k: int = 3):
    q_emb = embed(query)
    results = collection.query(
        query_embeddings=[q_emb],
        n_results=k
    )
    # results["documents"] is a list of lists
    docs = results["documents"][0] if results["documents"] else []
    return docs
