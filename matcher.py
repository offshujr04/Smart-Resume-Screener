import os
import re
from typing import Tuple

# Incase of no llm api
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    SentenceTransformer = None

# chahgpt api 
try:
    import openai
except ImportError:
    openai = None

# gemini api
try:
    import google.generativeai as genai
except ImportError:
    genai = None



MODEL_NAME = "all-MiniLM-L6-v2"
_embedder = None


def get_embedder():
    global _embedder
    if _embedder is None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers not installed.")
        _embedder = SentenceTransformer(MODEL_NAME)
    return _embedder


def local_match_score(resume_text: str, job_desc: str) -> Tuple[float, dict]:
    embedder = get_embedder()
    a = embedder.encode([resume_text])
    b = embedder.encode([job_desc])
    sim = float(cosine_similarity(a, b)[0][0])
    score = round(sim * 100, 2)

    resume_low = set(re.findall(r"\w+", resume_text.lower()))
    job_low = set(re.findall(r"\w+", job_desc.lower()))
    common = sorted(list(resume_low & job_low))[:10]
    return score, {"method": "local_embed", "common_tokens": common}


def openai_match_score(resume_text: str, job_desc: str, api_key: str = None) -> Tuple[float, dict]:
    if openai is None:
        raise RuntimeError("openai not installed.")
    api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not provided.")
    openai.api_key = api_key

    prompt = (
        "You are an assistant comparing a resume and a job description.\n"
        "Rate the candidate fit 1–10, justify in 1–2 sentences, then list 5 matching skills.\n\n"
        f"Resume:\n{resume_text}\n\nJob Description:\n{job_desc}\n\nScore:"
    )

    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=300,
    )
    out = resp["choices"][0]["message"]["content"].strip()
    m = re.search(r"(\d+(?:\.\d+)?)", out)
    score = float(m.group(1)) * 10 if m and float(m.group(1)) <= 10 else float(m.group(1)) if m else 0.0
    return round(score, 2), {"method": "openai", "raw_output": out}

def gemini_match_score(resume_text: str, job_desc: str, api_key: str = None) -> Tuple[float, dict]:
    # """Online scoring using Google Gemini API"""
    if genai is None:
        raise RuntimeError("google-generativeai not installed.")
    api_key = api_key or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not provided.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = (
        "Compare this resume with the job description.\n"
        "Rate the candidate fit on a scale of 1–10, explain briefly, and list 5 matching skills.\n\n"
        f"Resume:\n{resume_text}\n\nJob Description:\n{job_desc}\n\nScore:"
    )

    response = model.generate_content(prompt)
    out = response.text.strip()
    m = re.search(r"(\d+(?:\.\d+)?)", out)
    score = float(m.group(1)) * 10 if m and float(m.group(1)) <= 10 else float(m.group(1)) if m else 0.0
    return round(score, 2), {"method": "gemini", "raw_output": out}


def normalize_skills(skills):
    # accept either string or list
    if skills is None:
        return []
    if isinstance(skills, str):
        parts = [p.strip() for p in re.split(r"[,;|\\n]+", skills) if p.strip()]
    else:
        parts = [str(p).strip() for p in skills if p and str(p).strip()]

    alias_map = {
        "node.js": "node",
        "nodejs": "node",
        "ci/cd": "ci-cd",
        "cicd": "ci-cd",
        "js": "javascript",
        "py": "python",
        "tf": "tensorflow",
        "cv": "opencv",
        "scikitlearn": "scikit-learn",
        "scikit learn": "scikit-learn",
    }

    categories = {
        "python": "language",
        "java": "language",
        "c": "language",
        "c++": "language",
        "r": "language",
        "javascript": "language",
        "sql": "language",
        "node": "runtime",
        "react": "framework",
        "flask": "framework",
        "django": "framework",
        "streamlit": "framework",
        "fastapi": "framework",
        "pandas": "library",
        "numpy": "library",
        "scikit-learn": "library",
        "tensorflow": "library",
        "pytorch": "library",
        "docker": "tool",
        "kubernetes": "tool",
        "aws": "cloud",
        "gcp": "cloud",
        "azure": "cloud",
        "git": "tool",
    }

    seen = set()
    out = []
    for p in parts:
        orig = p
        low = p.lower().strip()
        # normalize some punctuation
        low = low.replace(".", "").replace("/", "-")
        low = re.sub(r"[^a-z0-9+\-#]+", "-", low)
        low = low.strip("-")
        canonical = alias_map.get(low, low)
        canonical = canonical.replace(" ", "-")
        if canonical in seen:
            continue
        seen.add(canonical)
        cat = categories.get(canonical, "other")
        out.append({"original": orig, "skill": canonical, "category": cat})

    return out
