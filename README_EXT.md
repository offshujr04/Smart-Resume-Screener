# Smart Resume Screener — Extended Documentation

This extended README contains architecture details, LLM prompts, implementation notes and next steps for the Smart Resume Screener project.

## Project overview

Smart Resume Screener is a lightweight demo that:
- Parses resumes (PDF/TXT) to extract contacts, education, skills and estimate years of experience.
- Normalizes skills into canonical tokens with categories.
- Matches resumes to a job description using either a local embedding model or LLMs (OpenAI / Gemini) and returns a numeric fit score.

Core files:
- `app.py` — Streamlit front-end.
- `resume_parser.py` — text extraction and heuristics.
- `matcher.py` — local embedding matcher + OpenAI/Gemini helpers + skill normalization.
- `db.py` — SQLAlchemy model + helpers to persist parsed resumes.

## LLM prompts (copy/paste-ready)

Skill extraction (JSON-only)
```
You are a skills-extraction assistant.
Extract only technical skills from the resume below and return a single JSON object with key "skills" containing an array of short skill strings.
Example output:
{"skills": ["python", "pandas", "docker"]}

Resume:
<resume_text>

Return JSON only.
```

Scoring / judgement (freeform — current implementation)
```
You are an assistant comparing a resume and a job description.
Rate the candidate fit on a scale of 1-10, justify in 1-2 sentences, and list up to 5 matching skills.

Resume:
<resume_text>

Job Description:
<job_description>

Return your answer in plain text (the code will extract the first numeric token found).
```

Recommended: Use JSON-only output or function-calling for robust parsing.

## Implementation notes & gotchas

- `resume_parser.py` uses spaCy NER when available; if `en_core_web_sm` is missing, it falls back to a blank pipeline.
- PDF extraction uses PyPDF2; scanned PDFs need OCR.
- Skill extraction is either: substring lookup in `COMMON_SKILLS` (fast, local) or dynamic extraction using an LLM when OpenAI/Gemini is selected.
- LLM output parsing is intentionally tolerant — the code attempts JSON extraction first, then bracket/CSV extraction, then token fallback.
- `normalize_skills` canonicalizes tokens and maps a subset of tokens to simple categories (language, framework, library, tool, cloud, runtime, other).
- `db.py` stores `skills` as a CSV string. For querying, convert to a normalized relation or JSON column.

## Running locally

1. Create virtualenv and install requirements:
```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. (Optional) Set API keys in environment:
```powershell
$env:OPENAI_API_KEY = "sk-..."
$env:GEMINI_API_KEY = "..."
```

3. Run Streamlit UI:
```powershell
streamlit run app.py
```

## Next steps I can implement

- Convert LLM calls to structured JSON (OpenAI function-calling) for robust parsing.
- Add spaCy PhraseMatcher + `skills_vocab.json` for high-quality extraction.
- Persist normalized skills into the DB as JSON and add filters in the UI.
- Add unit tests for parser and matcher (mock LLM responses).

If you'd like any of the above, tell me which and I will implement it.
