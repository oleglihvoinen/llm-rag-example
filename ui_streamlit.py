# ui_streamlit.py
import streamlit as st
import requests

API_URL = "http://127.0.0.1:8000/ask"

st.set_page_config(page_title="?? Local LLM Chat", page_icon="??", layout="centered")

st.title("?? Local LLM Chatbot")
st.caption("Powered by your RAG system (ChromaDB + FastAPI + Ollama/OpenAI)")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display past messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
user_input = st.chat_input("Ask something about your documents...")

if user_input:
    # Show user message
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Send request to FastAPI backend
    try:
        res = requests.post(API_URL, json={"question": user_input}, timeout=180)
        if res.status_code == 200:
            data = res.json()
            answer = data.get("answer", "?? No answer returned.")
        else:
            answer = f"? API Error: {res.status_code}"
    except Exception as e:
        answer = f"? Connection Error: {e}"

    # Display assistant reply
    st.chat_message("assistant").markdown(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
