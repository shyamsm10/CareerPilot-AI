import os
import json
import fitz  # PyMuPDF
import pdfplumber
from docx import Document
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Raw text extraction ────────────────────────────────────────────────────────

def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        doc = fitz.open(file_path)
        for page in doc:
            text += page.get_text() + "\n"
        doc.close()
    return text.strip()


def extract_text_from_docx(file_path: str) -> str:
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs if para.text.strip()])


def extract_raw_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Use PDF or DOCX.")


# ── LLM-powered structured extraction ─────────────────────────────────────────

EXTRACTION_PROMPT = """
You are a professional resume parser. Extract ALL information from the resume text below
and return ONLY a valid JSON object — no explanation, no markdown, no code fences.

Return this exact structure:
{{
  "name": "full name or empty string",
  "email": "email or empty string",
  "phone": "phone or empty string",
  "linkedin": "linkedin url or empty string",
  "github": "github url or empty string",
  "location": "city/state/country or empty string",
  "summary": "professional summary or empty string",
  "education": [
    {{
      "degree": "degree name",
      "field": "field of study",
      "institution": "college/university name",
      "year": "graduation year or range",
      "cgpa": "cgpa/percentage or empty string"
    }}
  ],
  "experience": [
    {{
      "title": "job title",
      "company": "company name",
      "duration": "start - end dates",
      "description": "responsibilities and achievements",
      "type": "internship or full-time or part-time"
    }}
  ],
  "projects": [
    {{
      "name": "project name",
      "description": "what it does",
      "technologies": ["tech1", "tech2"],
      "link": "github/demo link or empty string"
    }}
  ],
  "skills": {{
    "programming_languages": ["Python", "Java"],
    "frameworks": ["Flask", "React"],
    "tools": ["Git", "Docker"],
    "databases": ["MySQL", "MongoDB"],
    "cloud": ["AWS", "GCP"],
    "other": ["Machine Learning", "NLP"]
  }},
  "certifications": [
    {{
      "name": "certification name",
      "issuer": "issuing organization",
      "year": "year or empty string"
    }}
  ],
  "achievements": ["achievement 1", "achievement 2"],
  "languages": ["English", "Hindi"],
  "experience_level": "fresher or junior or mid or senior"
}}

Resume text:
{resume_text}
"""


def parse_resume_with_llm(raw_text: str) -> dict:
    prompt = EXTRACTION_PROMPT.format(resume_text=raw_text[:6000])

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You are a precise resume parser. Return only valid JSON, nothing else."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.1,
        max_tokens=2000
    )

    raw_output = response.choices[0].message.content.strip()

    if raw_output.startswith("```"):
        raw_output = raw_output.split("```")[1]
        if raw_output.startswith("json"):
            raw_output = raw_output[4:]
    raw_output = raw_output.strip()

    return json.loads(raw_output)


# ── Main agent function ────────────────────────────────────────────────────────

def run_resume_parser(file_path: str) -> dict:
    """
    Main entry point for Agent 1.
    Takes a resume file path, returns structured profile dict + saves to SQLite.
    """
    print(f"[Agent 1] Reading resume: {file_path}")

    raw_text = extract_raw_text(file_path)
    print(f"[Agent 1] Extracted {len(raw_text)} characters of text")

    if len(raw_text) < 50:
        raise ValueError("Resume text too short — check if the file is readable or not scanned.")

    print("[Agent 1] Sending to Groq LLM for structured extraction...")
    profile = parse_resume_with_llm(raw_text)

    # ── Save to SQLite ───────────────────────────────────────────
    try:
        from db import save_resume
        user_id = os.getenv("USER_ID", "default_user")
        profile_with_text = {**profile, "raw_text": raw_text}
        save_resume(user_id, profile_with_text)
        print(f"[Agent 1] Saved to SQLite for user: {user_id}")
    except Exception as e:
        print(f"[Agent 1] DB save skipped: {e}")
    # ────────────────────────────────────────────────────────────

    print("[Agent 1] Done. Profile extracted successfully.")
    return {
        "raw_text": raw_text,
        "profile": profile
    }


# ── Quick test ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python resume_parser.py <path_to_resume.pdf>")
        sys.exit(1)

    result = run_resume_parser(sys.argv[1])

    print("\n" + "="*50)
    print("EXTRACTED PROFILE:")
    print("="*50)
    print(json.dumps(result["profile"], indent=2))

    output_path = "parsed_resume.json"
    with open(output_path, "w") as f:
        json.dump(result["profile"], f, indent=2)
    print(f"\nSaved to {output_path}")
