# ui_streamlit.py
import streamlit as st
import requests

st.set_page_config(page_title="LLM RAG Demo", page_icon="🧠")

st.title("🧠 LLM RAG Demo")
st.write("Ask a question about your local documents.")

user_query = st.text_input("Your question")

if st.button("Ask") and user_query:
    try:
        resp = requests.post("http://localhost:8000/chat", json={"query": user_query})
        data = resp.json()
        st.subheader("Answer")
        st.write(data["answer"])

        with st.expander("Context used"):
            for i, c in enumerate(data["context"], 1):
                st.markdown(f"**Doc {i}:**")
                st.write(c)
    except Exception as e:
        st.error(f"Error calling API: {e}")
