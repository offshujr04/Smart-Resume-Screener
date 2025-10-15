import streamlit as st
import pandas as pd
from resume_parser import parse_pdf_bytes, parse_resume_text
from matcher import (
    local_match_score,
    openai_match_score,
    gemini_match_score,
    normalize_skills,
)
from db import get_session, save_resume

st.set_page_config(page_title="Smart Resume Screener", layout="wide")
st.title("Smart Resume Screener")

# Sidebar for the site
with st.sidebar:
    st.header("Options")
    scoring_method = st.selectbox("Choose Scoring method", ["Normal semantic method", "OpenAI GPT", "Gemini"])
    openai_key = st.text_input("OpenAI API Key", type="password") if scoring_method == "OpenAI GPT" else None
    gemini_key = st.text_input("Gemini API Key", type="password") if scoring_method == "Gemini" else None
    persist = st.checkbox("Save parsed resumes to local database", value=True)

# Resume uploading
uploaded = st.file_uploader(
    "Upload one or more resumes (PDF/TXT)",
    accept_multiple_files=True,
    type=["pdf", "txt"],
)
job_description = st.text_area("Paste job description here", height=250)

# Button action
if st.button("Process and Match"):
    if not uploaded:
        st.warning("Please upload at least one resume.")
    elif not job_description.strip():
        st.warning("Please paste a job description.")
    else:
        results = []
        sess = get_session() if persist else None
        progress = st.progress(0)
        total = len(uploaded)

        for i, f in enumerate(uploaded):
            # Naming and reading the file
            name = f.name
            data = f.read()
            try:
                parsed = parse_pdf_bytes(data) if f.type == "application/pdf" or name.lower().endswith(".pdf") \
                         else parse_resume_text(data.decode("utf-8", errors="ignore"))
            except Exception as e:
                st.error(f"Error parsing {name}: {e}")
                continue

            if persist and sess:
                try:
                    save_resume(sess, parsed)
                except Exception as e:
                    st.warning(f"Could not save {name}: {e}")

            try:
                score, meta = (
                    openai_match_score(parsed["full_text"], job_description, api_key=openai_key)
                    if scoring_method == "openai"
                    else local_match_score(parsed["full_text"], job_description)
                )
            except Exception as e:
                st.error(f"Scoring failed for {name}: {e}")
                score, meta = 0.0, {"error": str(e)}

            results.append({
                "filename": name,
                "name": parsed.get("name", ""),
                "emails": ",".join(parsed.get("emails", [])),
                "skills": ",".join(parsed.get("skills", [])),
                "skills_structured": normalize_skills(parsed.get("skills", [])),
                "years": parsed.get("years_experience_est", 0),
                "score": score,
                "meta": meta,
                "raw": parsed.get("full_text", ""),
            })
            progress.progress(int((i + 1) / total * 100))

        if results:
            df = pd.DataFrame(results).sort_values("score", ascending=False)
            st.subheader("Results")
            st.dataframe(df[["filename", "name", "emails", "skills", "years", "score"]])

            idx = st.selectbox("Select candidate to view details", df.index.tolist())
            r = df.loc[idx]
            st.markdown(f"### {r['filename']} — Score: {r['score']}")
            # st.write("Name:", r["name"])
            st.write("Emails:", r["emails"])
            # show structured skills if available
            try:
                structured = r["skills_structured"]
                if isinstance(structured, str):
                    st.write("Skills:", r["skills"])
                else:
                    st.write("Skills:")
                    for s in structured:
                        st.write(f"- {s.get('skill')} ({s.get('category')})")
            except Exception:
                st.write("Skills:", r["skills"])

            st.write("Years of experience:", r["years"])
            # st.write("Matcher meta:")
            # st.json(r["meta"])
            with st.expander("Full resume text"):
                st.text(r["raw"])

            st.download_button(
                "Download CSV",
                data=df.to_csv(index=False).encode("utf-8"),
                file_name="resume_match_results.csv",
            )
