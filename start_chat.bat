@echo off
title Local LLM Chat Launcher
color 0A
echo ===========================================
echo     🚀 Starting Local LLM Chatbot System
echo ===========================================
echo.

REM --- Step 1: Go to project folder ---
cd /d C:\llm-rag\llm-rag-example

REM --- Step 2: Activate virtual environment ---
echo Activating virtual environment...
call .venv\Scripts\activate.bat

REM --- Step 3: Start Ollama service in background ---
echo Starting Ollama service...
start "" powershell -WindowStyle Minimized -Command "ollama serve"
timeout /t 5 >nul

REM --- Step 4: Start FastAPI backend ---
echo Launching FastAPI backend...
start "" powershell -WindowStyle Minimized -Command "uvicorn app:app --reload"
timeout /t 5 >nul

REM --- Step 5: Launch Streamlit chat UI ---
echo Opening Streamlit Chat UI in browser...
start "" cmd /c "streamlit run ui_streamlit.py"

echo.
echo ===========================================
echo ✅ Local Chatbot is running!
echo FastAPI:   http://127.0.0.1:8000
echo Streamlit: http://localhost:8501
echo ===========================================
echo.
pause
