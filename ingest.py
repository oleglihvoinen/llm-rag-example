# ingest.py
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


# --- Ollama Embedding (universal) ---
def get_local_embedding(text: str) -> list[float]:
    """Generate embeddings via Ollama — with smart automatic fallback."""
    if not OLLAMA_VERSION:
        raise RuntimeError("❌ Ollama not reachable. Run 'ollama serve' first.")

    # Try /api/embeddings first (for new versions)
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
        # Create crude numeric embedding for compatibility
        return [float(ord(c)) / 1000 for c in content[:512]]
    except Exception as e:
        raise RuntimeError(f"Ollama legacy embedding failed: {e}")


# --- Unified Embedding Helper ---
def get_embedding(text: str) -> list[float]:
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
    # Fallback to Ollama
    return get_local_embedding(text)


# --- Read all .txt files from /data ---
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
    collection = chroma_client.get_or_create_collection("docs")

    docs = read_documents()
    if not docs:
        print("⚠️ No documents found in /data.")
        return

    print(f"📚 Found {len(docs)} document(s). Generating embeddings...")

    ids, texts, embeddings = [], [], []

    for i, (fname, content) in enumerate(docs):
        ids.append(f"doc-{i}")
        texts.append(content)
        embeddings.append(get_embedding(content))

    print("💾 Storing embeddings into Chroma...")
    collection.add(ids=ids, documents=texts, embeddings=embeddings)

    print("✅ Ingested", len(docs), "document(s) into ./chroma_db")


if __name__ == "__main__":
    main()
