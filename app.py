# app.py
from fastapi import FastAPI
from pydantic import BaseModel
from retriever import retrieve
import os
import requests
import subprocess, json
from dotenv import load_dotenv

# --- Load API key and init app ---
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
app = FastAPI(title="RAG Chat API")

# --- Input schema ---
class Query(BaseModel):
    question: str


# --- Helpers ---
def test_ollama():
    """Check if Ollama HTTP API is reachable."""
    try:
        r = requests.get("http://localhost:11434/api/version", timeout=3)
        return r.ok
    except Exception:
        return False

OLLAMA_HTTP_AVAILABLE = test_ollama()
print(f"🤖 Ollama HTTP API available: {OLLAMA_HTTP_AVAILABLE}")


def generate_via_cli(prompt: str) -> str:
    """Fallback to Ollama CLI if HTTP API fails."""
    try:
        result = subprocess.run(
            ["ollama", "run", "llama3", "--json"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        lines = [json.loads(l) for l in result.stdout.decode().splitlines() if l.strip()]
        text = "".join([l.get("response", "") for l in lines])
        return text.strip() or "⚠️ No output from Ollama CLI."
    except Exception as e:
        return f"❌ Ollama CLI error: {e}"


# --- Answer generation ---
def generate_answer(context: str, question: str) -> str:
    """Generate answer via OpenAI or Ollama fallback."""
    # Try OpenAI first
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant answering based on the given context."},
                    {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                ]
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            print(f"⚠️ OpenAI unavailable: {e}")

    # Try Ollama HTTP API
    if OLLAMA_HTTP_AVAILABLE:
        try:
            response = requests.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant answering based on the given context."},
                        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"}
                    ],
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "").strip() or "⚠️ Empty Ollama response."
        except Exception as e:
            print(f"⚠️ Ollama HTTP API failed: {e}")

    # Fallback: CLI
    print("💻 Using Ollama CLI fallback...")
    return generate_via_cli(f"Context:\n{context}\n\nQuestion: {question}")


# --- API endpoint ---
@app.post("/ask")
def ask(query: Query):
    """Handle a question -> retrieve context -> generate answer."""
    try:
        docs = retrieve(query.question, k=3)
        if not docs:
            return {"answer": "⚠️ No relevant documents found."}

        context = "\n\n".join(docs)
        answer = generate_answer(context, query.question)
        return {"answer": answer}
    except Exception as e:
        return {"answer": f"❌ Error: {e}"}


@app.get("/")
def root():
    return {"message": "✅ RAG Chat API running. POST /ask {'question': '...'}"}
