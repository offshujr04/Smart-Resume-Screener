import re
import io
from typing import Dict
import spacy

try:
    # pdf file reader
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

_nlp = None

def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except Exception:
            _nlp = spacy.blank("en")
    return _nlp


EMAIL_RE = re.compile(r"[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+")
PHONE_RE = re.compile(r"\+?\d[\d \-()]{6,}\d")
YEARS_RE = re.compile(r"(\d+)\s+years?")

COMMON_SKILLS = [
    "python", "java", "c++", "c", "c#", "r", "sql", "nosql", "matlab", "scala",
    "tensorflow", "pytorch", "keras", "scikit-learn", "opencv", "nltk", "spacy",
    "pandas", "numpy", "matplotlib", "seaborn", "plotly",
    "react", "angular", "vue", "next.js", "node.js", "express", "flask", "django", 
    "fastapi", "streamlit", "html", "css", "javascript", "typescript", 
    "bootstrap", "tailwindcss",
    "rest api", "graphql", "grpc",
    "docker", "kubernetes", "git", "github", "ci/cd", "jenkins", "linux", "bash", 
    "shell scripting", "agile", "scrum",
    "aws", "gcp", "azure", "firebase", "digitalocean",
    "mysql", "postgresql", "mongodb", "sqlite", "redis", "elasticsearch",
    "nlp", "computer vision", "deep learning", "machine learning", "data science", 
    "data analysis", "big data", "etl", "power bi", "tableau",
    "hadoop", "spark", "hive", "kafka", 
    "openai api", "langchain", "hugging face", "llm", "prompt engineering",
    "numba", "cuda", "parallel computing",
    "cybersecurity", "networking", "devops", "mlops", "apis", "microservices"
]



def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    if PdfReader is None:
        raise RuntimeError("PyPDF2 not installed.")
    reader = PdfReader(io.BytesIO(pdf_bytes))
    return "\n".join([p.extract_text() or "" for p in reader.pages])


def parse_resume_text(text: str) -> Dict:
    nlp = _get_nlp()
    doc = nlp(text)

    emails = EMAIL_RE.findall(text)
    phones = PHONE_RE.findall(text)

    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
            break

    education, edu_keywords = [], [
        "bachelor", "master", "phd", "b.sc", "btech", "m.tech", "mba",
        "msc", "bs", "ms", "degree"
    ]
    for line in text.splitlines():
        l = line.lower()
        if any(k in l for k in edu_keywords) and len(line.split()) < 12:
            education.append(line.strip())

    skills = {s for s in COMMON_SKILLS if s in text.lower()}

    years = sum(int(m.group(1)) for m in YEARS_RE.finditer(text.lower()))

    return {
        "name": name or "",
        "emails": emails,
        "phones": phones,
        "education": education,
        "skills": sorted(list(skills)),
        "years_experience_est": years,
        "full_text": text
    }


def parse_pdf_bytes(pdf_bytes: bytes) -> Dict:
    text = extract_text_from_pdf_bytes(pdf_bytes)
    return parse_resume_text(text)
