# LLM RAG Example (Local Docs → Chatbot)

This is a minimal Retrieval-Augmented Generation (RAG) example in Python.

- load text files from `data/`
- create embeddings
- store them in ChromaDB
- expose a chat endpoint with FastAPI
- optional Streamlit UI to chat with your docs

## 1. Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
