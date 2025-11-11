# ingest.py
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

# simple embedding wrapper
def get_embedding(text: str) -> list[float]:
    res = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return res.data[0].embedding

def read_documents(data_dir="data"):
    docs = []
    for fname in os.listdir(data_dir):
        if fname.endswith(".txt"):
            with open(os.path.join(data_dir, fname), "r", encoding="utf-8") as f:
                docs.append((fname, f.read()))
    return docs

def main():
    # create / connect to local chroma db
    chroma_client = chromadb.Client(Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory="chroma_db"
    ))

    collection = chroma_client.get_or_create_collection("docs")

    docs = read_documents()
    if not docs:
        print("No documents found in data/")
        return

    ids = []
    texts = []
    embeddings = []

    for i, (fname, content) in enumerate(docs):
        ids.append(f"doc-{i}")
        texts.append(content)
        embeddings.append(get_embedding(content))

    collection.add(
        ids=ids,
        documents=texts,
        embeddings=embeddings
    )

    chroma_client.persist()
    print(f"Ingested {len(docs)} documents into Chroma.")

if __name__ == "__main__":
    main()
