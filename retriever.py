# retriever.py
import os
import json
import requests
from dotenv import load_dotenv
from chromadb import PersistentClient

# --- Load environment variables ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Setup OpenAI client ---
use_openai = False
try:
    if OPENAI_API_KEY:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        use_openai = True
        print("🧠 Using OpenAI for embeddings.")
    else:
        print("⚠️ No OPENAI_API_KEY found. Using Ollama for local embeddings.")
except Exception:
    print("⚠️ OpenAI not available. Using Ollama for local embeddings.")


# --- Ollama version detection ---
def get_ollama_version() -> str:
    """Return Ollama version string, or empty if not available."""
    try:
        resp = requests.get("http://localhost:11434/api/version", timeout=3)
        if resp.ok:
            data = resp.json()
            return data.get("version", "")
    except Exception:
        pass
    return ""


OLLAMA_VERSION = get_ollama_version()
if OLLAMA_VERSION:
    print(f"🤖 Detected Ollama version: {OLLAMA_VERSION}")
else:
    print("⚠️ Ollama not reachable — ensure it's running with 'ollama serve'.")


# --- Ollama embedding (modern + fallback) ---
def get_local_embedding(text: str) -> list[float]:
    """Generate embeddings via Ollama — auto-fallback between endpoints."""
    if not OLLAMA_VERSION:
        raise RuntimeError("❌ Ollama not reachable. Run 'ollama serve' first.")

    # Try /api/embeddings first
    url = "http://localhost:11434/api/embeddings"
    data = {"model": "nomic-embed-text", "prompt": text}
    try:
        r = requests.post(url, json=data)
        if r.status_code == 404:
            print("⚙️ /api/embeddings not found — switching to /api/generate fallback.")
            return get_ollama_embedding_fallback(text)
        r.raise_for_status()
        return r.json()["embedding"]
    except Exception as e:
        print(f"⚠️ Ollama embeddings API failed: {e}. Retrying with fallback...")
        return get_ollama_embedding_fallback(text)


def get_ollama_embedding_fallback(text: str) -> list[float]:
    """Fallback for older Ollama versions that lack /api/embeddings."""
    url = "http://localhost:11434/api/generate"
    data = {
        "model": "nomic-embed-text",
        "prompt": f"Return a numeric vector embedding for: {text[:200]}",
        "stream": False
    }
    try:
        r = requests.post(url, json=data)
        r.raise_for_status()
        result = r.json()
        content = result.get("response", "")
        # crude numeric fallback embedding
        return [float(ord(c)) / 1000 for c in content[:512]]
    except Exception as e:
        raise RuntimeError(f"Ollama legacy embedding failed: {e}")


# --- Unified embedding helper ---
def embed(text: str) -> list[float]:
    """Use OpenAI if available, otherwise Ollama."""
    global use_openai
    if use_openai:
        try:
            res = client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            return res.data[0].embedding
        except Exception as e:
            if "insufficient_quota" in str(e) or "429" in str(e):
                print("🚫 OpenAI quota reached — switching to Ollama.")
                use_openai = False
            else:
                raise
    return get_local_embedding(text)


# --- Connect to Chroma ---
chroma_client = PersistentClient(path="chroma_db")
collection = chroma_client.get_or_create_collection("docs")


# --- Retrieve top-k similar docs ---
def retrieve(query: str, k: int = 3):
    q_emb = embed(query)
    results = collection.query(query_embeddings=[q_emb], n_results=k)
    if not results["documents"]:
        return []
    return results["documents"][0]


# --- Manual test run ---
if __name__ == "__main__":
    test_query = "What is this project about?"
    docs = retrieve(test_query, k=2)
    print(f"\n🔍 Query: {test_query}")
    print("Top results:")
    for d in docs:
        print(f"- {d[:120]}...")
