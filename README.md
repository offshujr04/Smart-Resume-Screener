# Smart Resume Screener

Lightweight resume parsing + LLM-powered matching demo.

Components
- FastAPI backend: `backend/app.py`
- Streamlit frontend: `streamlit_app.py`
- SQLite DB: `resumes.db` (created automatically)

Setup
1. Create a virtual environment and install requirements:

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt
```

2. (Optional) Set `OPENAI_API_KEY` environment variable to enable real LLM scoring.
3. Start backend:

```powershell
cd backend; uvicorn app:app --reload --port 8000
```

4. Start Streamlit UI:

```powershell
streamlit run streamlit_app.py
```

Notes
- The repo includes a simple `skills.txt` file used by the extractor.
- LLM prompt is in `backend/llm.py` and returns a JSON with score and justification.

Security
- Don't commit `OPENAI_API_KEY` to source control.

Next steps
- Improve skill extraction with NLP, add embeddings-based semantic search, and add tests.
