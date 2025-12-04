# ingest.py
import os
import json
import requests
from dotenv import load_dotenv
from chromadb import PersistentClient
from chromadb.utils import embedding_functions

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Setup OpenAI client ---
use_openai = False
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        use_openai = True
        print("🧠 Using OpenAI for embeddings.")
    else:
        print("⚠️ No OPENAI_API_KEY found. Using Ollama for embeddings.")
except Exception:
    print("⚠️ OpenAI not available. Using Ollama for embeddings.")


# --- Ollama version detection ---
def get_ollama_version() -> str:
    try:
        resp = requests.get("http://localhost:11434/api/version", timeout=3)
        if resp.ok:
            return resp.json().get("version", "")
    except Exception:
        pass
    return ""


OLLAMA_VERSION = get_ollama_version()
if OLLAMA_VERSION:
    print(f"🤖 Detected Ollama version: {OLLAMA_VERSION}")
else:
    print("⚠️ Ollama not reachable — ensure it's running with 'ollama serve'.")


# --- Ollama Embedding Logic ---
def get_local_embedding(text: str) -> list[float]:
    """Generate embeddings via Ollama."""
    if not OLLAMA_VERSION:
        raise RuntimeError("❌ Ollama not reachable. Run 'ollama serve' first.")

    url = "http://localhost:11434/api/embeddings"
    data = {"model": "nomic-embed-text", "prompt": text}

    try:
        r = requests.post(url, json=data)
        if r.status_code == 404:
            print("⚙️ /api/embeddings unavailable — fallback to /api/generate.")
            return get_ollama_embedding_fallback(text)
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        print(f"⚠️ Embedding error: {e}. Fallback in use.")
        return get_ollama_embedding_fallback(text)


def get_ollama_embedding_fallback(text: str) -> list[float]:
    """Legacy fallback for older Ollama versions."""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "nomic-embed-text",
        "prompt": f"Return a numeric embedding for: {text[:240]}",
        "stream": False
    }

    r = requests.post(url, json=data)
    r.raise_for_status()
    content = r.json().get("response", "")
    return [float(ord(c)) / 1000 for c in content[:512]]


# --- Unified Embedding Helper ---
def get_embedding(text: str) -> list[float]:
    """Use OpenAI if available, otherwise Ollama."""
    global use_openai

    # --- OpenAI path ---
    if use_openai:
        try:
            res = openai_client.embeddings.create(
                model="text-embedding-3-small",  # 1536 dims
                input=text
            )
            return res.data[0].embedding
        except Exception as e:
            if "insufficient_quota" in str(e) or "429" in str(e):
                print("🚫 OpenAI quota reached — switching to Ollama.")
                use_openai = False
            else:
                raise

    # --- Ollama fallback (768 dims) ---
    return get_local_embedding(text)


# --- Chroma Collection Constructor (fixed) ---
def create_collection(chroma_client):
    """
    Build a Chroma collection with the correct embedding dimension.
    - OpenAI → 1536 dims → docs_openai
    - Ollama → 768 dims → docs_local
    """
    global use_openai

    if use_openai:
        print("📌 Using OpenAI embedding function (1536 dims)")
        ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=OPENAI_API_KEY,
            model_name="text-embedding-3-small"
        )
        collection_name = "docs_openai"
    else:
        print("📌 Using local embedding function (768 dims)")
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="nomic-embed-text"
        )
        collection_name = "docs_local"

    return chroma_client.get_or_create_collection(
        name=collection_name,
        embedding_function=ef
    )


# --- Read text files from /data ---
def read_documents(data_dir="data"):
    docs = []
    for fname in os.listdir(data_dir):
        if fname.endswith(".txt"):
            with open(os.path.join(data_dir, fname), "r", encoding="utf-8") as f:
                docs.append((fname, f.read()))
    return docs


# --- Main ingestion workflow ---
def main():
    print("🔍 Connecting to Chroma database...")
    chroma_client = PersistentClient(path="chroma_db")

    collection = create_collection(chroma_client)

    docs = read_documents()
    if not docs:
        print("⚠️ No documents found in /data.")
        return

    print(f"📚 Found {len(docs)} document(s). Generating embeddings...")

    ids, contents, vectors = [], [], []

    for i, (fname, content) in enumerate(docs):
        ids.append(f"doc-{i}")
        contents.append(content)
        vectors.append(get_embedding(content))

    print("💾 Storing embeddings into Chroma...")
    collection.add(ids=ids, documents=contents, embeddings=vectors)

    print("✅ Ingested", len(docs), "document(s) into ./chroma_db")


if __name__ == "__main__":
    main()
