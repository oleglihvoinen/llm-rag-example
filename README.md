
# 💬 Local LLM RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** chatbot powered by **Ollama**, **ChromaDB**, and **FastAPI** — with an optional **Streamlit UI** for interactive chat.  
The system can run entirely **offline** using local LLMs (like `llama3`) or connect to **OpenAI** when available.

---

## 🚀 Features

✅ **Completely local or hybrid AI**
- Works with **OpenAI API** or **Ollama** models (local inference)  
- Auto-detects your available backend

✅ **Retrieval-Augmented Generation (RAG)**
- Uses **ChromaDB** to store and retrieve document embeddings  
- Answers based on your uploaded `.txt` data

✅ **Unified backend**
- Built with **FastAPI** for fast RESTful communication  
- Easy integration with other frontends

✅ **Interactive UI**
- Beautiful **Streamlit chat interface**
- Maintains conversational history
- One-click Windows launch script

---

## 🧠 Architecture Overview

```text
+-----------------------+
|  Text Documents (.txt)|
+----------+------------+
           |
           v
     [ ingest.py ]
           |
           v
  +-----------------+
  |   ChromaDB Store |
  +-----------------+
           |
           v
     [ retriever.py ]
           |
           v
     [ app.py (FastAPI) ]
           |
           v
     [ ui_streamlit.py ]
````

---

## 🧩 Components

| File                                    | Description                                                                     |
| --------------------------------------- | ------------------------------------------------------------------------------- |
| **`ingest.py`**                         | Reads text files → generates embeddings (OpenAI or Ollama) → stores in ChromaDB |
| **`retriever.py`**                      | Retrieves top relevant documents for a given question                           |
| **`app.py`**                            | FastAPI backend for Q&A requests                                                |
| **`ui_streamlit.py`**                   | Browser-based chat interface                                                    |
| **`start_chat.bat` / `start_chat.ps1`** | One-click launchers for Windows                                                 |
| **`requirements.txt`**                  | Full list of dependencies                                                       |

---

## ⚙️ Installation

### 1️⃣ Clone the repository

```bash
git clone https://github.com/oleglihvoinen/llm-rag-example.git
cd llm-rag-example
```

### 2️⃣ Create a virtual environment

```bash
python -m venv .venv
.\.venv\Scripts\activate
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ (Optional) Add your OpenAI API key

Create a `.env` file:

```bash
OPENAI_API_KEY=your_key_here
```

---

## 🤖 Ollama Setup

1. [Download Ollama](https://ollama.com/download)
2. Pull your preferred local model (e.g., Llama 3):

   ```bash
   ollama pull llama3
   ```
3. Start the Ollama server:

   ```bash
   ollama serve
   ```

---

## 🧱 Prepare Your Data

Place your `.txt` documents inside the `data/` folder, then run:

```bash
python ingest.py
```

✅ This creates a local ChromaDB database (`/chroma_db`) with your text embeddings.

---

## 💬 Run the Chatbot

### 🪄 Option 1 – One-click (Windows)

Double-click:

```
start_chat.bat
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.

### 🧩 Option 2 – Manual startup

```bash
ollama serve
uvicorn app:app --reload
streamlit run ui_streamlit.py
```

---

## 🧠 Example Query

**Question:**

> What is this project about?

**Answer:**

> This project demonstrates a retrieval-augmented chatbot that uses local embeddings and large language models to answer questions based on custom documents.

---

## 🛠 Requirements

* Python **3.10+**
* Ollama **0.12+**
* ChromaDB **0.5+**
* (Optional) OpenAI API Key

---

## 📦 Requirements File

See [`requirements.txt`](./requirements.txt):

```text
fastapi
uvicorn
chromadb
openai
requests
python-dotenv
streamlit
pydantic
tiktoken
```

---

## 🌐 Project Structure

```text
llm-rag-example/
│
├── app.py
├── retriever.py
├── ingest.py
├── ui_streamlit.py
├── requirements.txt
├── start_chat.bat
├── start_chat.ps1
├── data/
│   └── example.txt
└── chroma_db/
```

---

## 📘 License

This project is released under the **MIT License** — free for personal and educational use.

---

## 🧩 Credits

Created by **Oleg Lihvoinen**
Built with ❤️ using:

* [FastAPI](https://fastapi.tiangolo.com)
* [Streamlit](https://streamlit.io)
* [Ollama](https://ollama.com)
* [ChromaDB](https://www.trychroma.com)
* [OpenAI](https://platform.openai.com)

---

## 🖼️ Optional Screenshot

![Architecture Diagram](/assets/images/llm2.png)

---

> 💡 **Tip:** This setup allows you to run an entirely offline local AI assistant.
> You can expand it to include PDFs, SQL data, or internal documents — simply adapt `ingest.py` to your preferred data source.

```

---

