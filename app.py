# app.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI

from retriever import retrieve

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set in .env")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI(title="LLM RAG Example")

class ChatRequest(BaseModel):
    query: str

class ChatResponse(BaseModel):
    answer: str
    context: list[str]

def build_prompt(user_query: str, context_docs: list[str]) -> str:
    context_text = "\n\n".join(context_docs)
    return (
        "You are a helpful assistant. Use the context below to answer.\n\n"
        f"CONTEXT:\n{context_text}\n\n"
        f"USER QUESTION: {user_query}\n\n"
        "If the answer is not in the context, say you don't know."
    )

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    docs = retrieve(req.query, k=3)
    prompt = build_prompt(req.query, docs)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer based on provided context."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
    )

    answer = completion.choices[0].message.content
    return ChatResponse(answer=answer, context=docs)
