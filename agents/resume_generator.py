"""
agents/resume_generator.py — Agent 5
Generates the final resume in BOTH plain text + PDF formats.
Auto-generates optimized PDF when ATS score is low.
"""

import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.1-8b-instant"

# ── PDF imports (only if reportlab is installed) ──────────────────────────────
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.enums import TA_CENTER
    PDF_ENABLED = True
except ImportError:
    PDF_ENABLED = False
    print("[Agent 5] reportlab not installed — PDF generation disabled. Run: pip install reportlab")


# ── Plain text resume generation ──────────────────────────────────────────────

def generate_resume(profile: dict, ats_result: dict, role: str) -> str:
    rewritten = ats_result.get("rewritten_content", {})

    exp_bullets = ""
    for exp in rewritten.get("experience", []):
        exp_bullets += f"\n{exp['title']} | {exp['company']}\n"
        for b in exp.get("bullets", []):
            exp_bullets += f"• {b}\n"

    proj_bullets = ""
    for proj in rewritten.get("projects", []):
        proj_bullets += f"\n{proj['name']}\n"
        for b in proj.get("bullets", []):
            proj_bullets += f"• {b}\n"

    skills = profile.get("skills", {})
    all_skills = (
        skills.get("programming_languages", []) +
        skills.get("frameworks", []) +
        skills.get("tools", []) +
        skills.get("other", [])
    )

    certs = " | ".join([f"{c['name']} – {c['issuer']}" for c in profile.get("certifications", [])])
    edu = profile.get("education", [{}])[0]

    prompt = f"""Create a clean ATS-friendly resume in plain text for a {role} role.

Candidate info:
Name: {profile.get('name')}
Email: {profile.get('email')} | Phone: {profile.get('phone')} | LinkedIn: {profile.get('linkedin')}
Location: {profile.get('location')}

Education: {edu.get('degree')} in {edu.get('field')} | {edu.get('institution')} | {edu.get('year')}

Experience:{exp_bullets}

Projects:{proj_bullets}

Skills: {', '.join(all_skills[:20])}
Certifications: {certs}

Format it as a professional resume with clear sections. Use plain text only, no markdown symbols.
Keep it to one page. Make the summary sharp and targeted for {role}."""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=1200
    )
    return r.choices[0].message.content.strip()


# ── PDF generation ────────────────────────────────────────────────────────────

def build_resume_pdf(profile: dict, ats_result: dict, role: str, output_path: str) -> str:
    """Build clean ATS-friendly PDF from profile + ats optimized content."""
    if not PDF_ENABLED:
        return None

    rewritten = ats_result.get("rewritten_content", {})

    name = profile.get("name", "Your Name")
    email = profile.get("email", "")
    phone = profile.get("phone", "")
    linkedin = profile.get("linkedin", "")
    github = profile.get("github", "")
    location = profile.get("location", "")

    # Use rewritten optimized content if available, else raw profile
    summary = rewritten.get("summary", profile.get("summary", f"Driven {role} with hands-on experience building real-world projects."))
    skills = rewritten.get("skills", profile.get("skills", {}))
    experience = rewritten.get("experience", profile.get("experience", []))
    projects = rewritten.get("projects", profile.get("projects", []))
    education = profile.get("education", [])
    certs = profile.get("certifications", [])

    doc = SimpleDocTemplate(
        output_path, pagesize=letter,
        rightMargin=0.5*inch, leftMargin=0.5*inch,
        topMargin=0.5*inch, bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    name_style = ParagraphStyle('Name', parent=styles['Heading1'], fontSize=18,
                                 spaceAfter=2, alignment=TA_CENTER,
                                 fontName='Helvetica-Bold', textColor=HexColor('#1a1a1a'))
    contact_style = ParagraphStyle('Contact', parent=styles['Normal'], fontSize=9,
                                    alignment=TA_CENTER, spaceAfter=8,
                                    textColor=HexColor('#444444'))
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontSize=12,
                                    spaceBefore=10, spaceAfter=4,
                                    fontName='Helvetica-Bold', textColor=HexColor('#1a1a1a'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=12, spaceAfter=3)
    bullet_style = ParagraphStyle('Bullet', parent=body_style, leftIndent=12, spaceAfter=2)

    story = []

    # Header
    story.append(Paragraph(name.upper(), name_style))
    contact_parts = [p for p in [email, phone, location, linkedin, github] if p]
    story.append(Paragraph(" | ".join(contact_parts), contact_style))

    # Summary
    story.append(Paragraph("PROFESSIONAL SUMMARY", section_style))
    story.append(Paragraph(summary, body_style))
    story.append(Spacer(1, 4))

    # Skills
    if skills:
        story.append(Paragraph("SKILLS", section_style))
        if isinstance(skills, dict):
            for category, skill_list in skills.items():
                if skill_list and isinstance(skill_list, list):
                    cat_name = category.replace("_", " ").title()
                    story.append(Paragraph(f"<b>{cat_name}:</b> {', '.join(skill_list)}", body_style))
        else:
            story.append(Paragraph(", ".join(skills), body_style))
        story.append(Spacer(1, 4))

    # Experience
    if experience:
        story.append(Paragraph("EXPERIENCE", section_style))
        for exp in experience:
            title = exp.get("title", exp.get("role", ""))
            company = exp.get("company", "")
            duration = exp.get("duration", "")
            description = exp.get("description", "")
            bullets = exp.get("bullets", [])

            header = f"<b>{title}</b> — {company}" if company else f"<b>{title}</b>"
            story.append(Paragraph(header, body_style))
            if duration:
                story.append(Paragraph(f"<i>{duration}</i>", body_style))

            if bullets:
                for b in bullets:
                    story.append(Paragraph(f"• {b}", bullet_style))
            elif description:
                for line in description.split("\n"):
                    if line.strip():
                        story.append(Paragraph(f"• {line.strip()}", bullet_style))
            story.append(Spacer(1, 4))

    # Projects
    if projects:
        story.append(Paragraph("PROJECTS", section_style))
        for proj in projects:
            pname = proj.get("name", "")
            pdesc = proj.get("description", "")
            techs = proj.get("technologies", proj.get("tech_stack", []))
            link = proj.get("link", "")
            bullets = proj.get("bullets", [])

            header = f"<b>{pname}</b>"
            if link:
                header += f" | {link}"
            story.append(Paragraph(header, body_style))
            if techs:
                story.append(Paragraph(f"<i>Tech: {', '.join(techs)}</i>", body_style))

            if bullets:
                for b in bullets:
                    story.append(Paragraph(f"• {b}", bullet_style))
            elif pdesc:
                for line in pdesc.split("\n"):
                    if line.strip():
                        story.append(Paragraph(f"• {line.strip()}", bullet_style))
            story.append(Spacer(1, 4))

    # Education
    if education:
        story.append(Paragraph("EDUCATION", section_style))
        for edu in education:
            degree = edu.get("degree", "")
            field = edu.get("field", "")
            inst = edu.get("institution", "")
            year = edu.get("year", "")
            cgpa = edu.get("cgpa", "")

            header = f"<b>{degree}</b>"
            if field:
                header += f", {field}"
            story.append(Paragraph(header, body_style))
            sub = inst
            if year:
                sub += f" | {year}"
            if cgpa:
                sub += f" | CGPA: {cgpa}"
            story.append(Paragraph(sub, body_style))
            story.append(Spacer(1, 4))

    # Certifications
    if certs:
        story.append(Paragraph("CERTIFICATIONS", section_style))
        for cert in certs:
            cname = cert.get("name", "")
            cissuer = cert.get("issuer", "")
            cyear = cert.get("year", "")
            line = f"• <b>{cname}</b>"
            if cissuer:
                line += f" — {cissuer}"
            if cyear:
                line += f" ({cyear})"
            story.append(Paragraph(line, body_style))
        story.append(Spacer(1, 4))

    doc.build(story)
    return os.path.abspath(output_path)


# ── Main entry point ──────────────────────────────────────────────────────────

def run_resume_generator(profile: dict, ats_result: dict, career_goal_result: dict) -> dict:
    role = career_goal_result["normalized_role"]
    name_slug = (profile.get("name") or "user").lower().replace(" ", "_")

    print(f"[Agent 5] Generating ATS-optimized resume for {role}...")

    # ── Step 1: Generate plain text resume ──
    resume_text = generate_resume(profile, ats_result, role)

    # ── Step 2: Generate PDF ──
    pdf_path = None
    ats_score = ats_result.get("optimized_ats_score", ats_result.get("original_ats_score", 0))

    if PDF_ENABLED:
        try:
            pdf_filename = f"optimized_resume_{name_slug}.pdf"
            pdf_path = build_resume_pdf(profile, ats_result, role, pdf_filename)
            print(f"[Agent 5] ✓ PDF generated: {pdf_path}")
        except Exception as e:
            print(f"[Agent 5] PDF generation failed: {e}")
            pdf_path = None
    else:
        print(f"[Agent 5] PDF skipped (install reportlab: pip install reportlab)")

    # ── Step 3: Auto-save text version ──
    txt_filename = f"generated_resume_{name_slug}.txt"
    with open(txt_filename, "w") as f:
        f.write(resume_text)
    print(f"[Agent 5] ✓ Text resume saved: {txt_filename}")

    # ── Step 4: Save to SQLite ──
    try:
        from db import get_conn
        user_id = os.getenv("USER_ID", "default_user")
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS generated_resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                ats_score REAL,
                pdf_path TEXT,
                txt_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            INSERT INTO generated_resumes (user_id, role, ats_score, pdf_path, txt_path)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, role, ats_score, pdf_path, txt_filename))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Agent 5] DB save warning: {e}")

    print(f"[Agent 5] Resume generated successfully.")

    return {
        "role": role,
        "resume_text": resume_text,
        "txt_path": os.path.abspath(txt_filename),
        "pdf_path": pdf_path,
        "ats_score": ats_score,
        "download_ready": pdf_path is not None
    }


# ── Quick test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open("parsed_resume.json") as f:
        profile = json.load(f)
    with open("ats_optimized.json") as f:
        ats_result = json.load(f)
    with open("career_goal_analysis.json") as f:
        career_goal_result = json.load(f)

    result = run_resume_generator(profile, ats_result, career_goal_result)

    print("\n" + "="*50)
    print(f"GENERATED RESUME — {result['role'].upper()}")
    print("="*50)
    print(result["resume_text"])

    print(f"\n{'='*50}")
    print(f"  📄 Text: {result['txt_path']}")
    if result['pdf_path']:
        print(f"  📄 PDF : {result['pdf_path']}")
    print(f"  📊 ATS Score: {result['ats_score']}/100")
    print(f"{'='*50}\n")
