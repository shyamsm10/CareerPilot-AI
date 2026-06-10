import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3-32b"


def safe_json(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)


# ── NEW: Role recommender ──────────────────────────────────────────────────
ROLE_PROFILES = {
    "AI Engineer":       ["Python","Machine Learning","Deep Learning","LLMs","RAG","LangChain","FastAPI","Docker","MLOps"],
    "Full Stack Developer": ["React","Node.js","JavaScript","REST APIs","SQL","MongoDB","Git","TypeScript","Docker"],
    "Data Scientist":    ["Python","Machine Learning","Statistics","Pandas","NumPy","Data Visualization","SQL","Scikit-learn","Jupyter"],
    "Data Analyst":      ["SQL","Excel","Power BI","Tableau","Python","Statistics","Data Visualization","Reporting"],
    "ML Engineer":       ["Python","Machine Learning","TensorFlow","PyTorch","MLOps","Docker","AWS","Model Deployment","Spark"],
    "Backend Developer": ["Python","FastAPI","REST APIs","SQL","Docker","AWS","Redis","Microservices","Git"],
    "DevOps Engineer":   ["Docker","Kubernetes","AWS","CI/CD","Linux","Terraform","Ansible","Git","Monitoring"],
}

def recommend_roles(profile: dict) -> dict:
    """Score resume against all roles and return ranked recommendations."""
    all_skills = []
    for cat in profile.get("skills", {}).values():
        if isinstance(cat, list):
            all_skills.extend([s.lower() for s in cat])
    skills_str = ", ".join(all_skills[:40])

    summary = profile.get("summary", "")
    projects = " ".join([p.get("name","") + " " + p.get("description","")[:100]
                         for p in profile.get("projects", [])])

    prompt = f"""Analyze this candidate profile and score them for each role (0-100).

Candidate skills: {skills_str}
Summary: {summary[:300]}
Projects: {projects[:400]}

Score these roles honestly based on current skills (not potential):
{json.dumps(list(ROLE_PROFILES.keys()))}

Respond with ONLY JSON. No thinking, no markdown.
{{"scores": {{"AI Engineer": 72, "Full Stack Developer": 45}}, "top_role": "AI Engineer", "reasoning": "Strong ML/LLM skills from projects"}}"""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=400
    )
    data = safe_json(r.choices[0].message.content)

    # Sort roles by score
    scores = data.get("scores", {})
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    data["ranked"] = [{"role": r, "score": s, "required_skills": ROLE_PROFILES.get(r, [])} for r, s in ranked]
    return data


def score_resume(resume_text: str, target_role: str, required_skills: list) -> dict:
    prompt = f"""Rate this resume for a {target_role} role. Required skills: {', '.join(required_skills)}

Resume:
{resume_text[:2000]}

Respond with ONLY a JSON object. No thinking, no explanation, no markdown.
{{"score": 75, "keyword_score": 80, "impact_score": 60, "issues": ["issue1"], "missing_keywords": ["kw1"]}}"""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1, max_tokens=400
    )
    return safe_json(r.choices[0].message.content)


def rewrite_bullets(experience: list, projects: list, role: str, missing_keywords: list) -> dict:
    exp_text = "\n".join([f"- {e['title']} at {e['company']}: {e.get('description','')[:200]}" for e in experience])
    proj_text = "\n".join([f"- {p['name']}: {p.get('description','')[:150]}" for p in projects])

    prompt = f"""Rewrite these resume bullets for a {role} role. Inject keywords: {', '.join(missing_keywords[:5])}
Use strong action verbs and add metrics where possible.

Experience:
{exp_text}

Projects:
{proj_text}

Respond with ONLY a JSON object. No thinking, no explanation, no markdown.
{{"experience": [{{"title": "title", "company": "company", "bullets": ["bullet1", "bullet2"]}}], "projects": [{{"name": "name", "bullets": ["bullet1"]}}]}}"""

    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3, max_tokens=800
    )
    return safe_json(r.choices[0].message.content)


def run_ats_optimizer(profile: dict, career_goal_result: dict) -> dict:
    role = career_goal_result["normalized_role"]
    required = career_goal_result["required_skills"]

    print("[Agent 4] Scoring original resume...")
    original_score = score_resume(
        profile.get("summary", "") + str(profile.get("experience", "")),
        role, required
    )

    print("[Agent 4] Rewriting bullets...")
    missing_kw = original_score.get("missing_keywords", [])
    rewritten = rewrite_bullets(
        profile.get("experience", []),
        profile.get("projects", []),
        role, missing_kw
    )

    print("[Agent 4] Scoring optimized resume...")
    new_score = score_resume(str(rewritten), role, required)

    result = {
        "role": role,
        "original_ats_score": original_score.get("score", 0),
        "optimized_ats_score": new_score.get("score", 0),
        "issues_fixed": original_score.get("issues", []),
        "keywords_added": missing_kw,
        "rewritten_content": rewritten
    }

    print(f"[Agent 4] ATS Score: {result['original_ats_score']}% → {result['optimized_ats_score']}%")
    return result


if __name__ == "__main__":
    with open("parsed_resume.json") as f:
        profile = json.load(f)

    # ── Role recommendation mode ──────────────────────────────────────────
    print("\n[Agent 4] Analyzing resume for best-fit roles...\n")
    rec = recommend_roles(profile)

    print("=" * 52)
    print("RECOMMENDED CAREER PATHS (based on your resume)")
    print("=" * 52)
    for item in rec["ranked"]:
        bar = "█" * (item["score"] // 10) + "░" * (10 - item["score"] // 10)
        print(f"  {item['role']:<26} {bar}  {item['score']}%")
    print(f"\n  Best fit: {rec['top_role']}")
    print(f"  Reason  : {rec.get('reasoning','')}")

    with open("role_recommendations.json", "w") as f:
        json.dump(rec, f, indent=2)
    print("\nSaved to role_recommendations.json")

    # ── Normal ATS optimization (if career_goal_analysis.json exists) ─────
    if os.path.exists("career_goal_analysis.json"):
        print("\n[Agent 4] Running ATS optimization for chosen goal...\n")
        with open("career_goal_analysis.json") as f:
            career_goal_result = json.load(f)
        result = run_ats_optimizer(profile, career_goal_result)
        with open("ats_optimized.json", "w") as f:
            json.dump(result, f, indent=2)
        print(f"\nOriginal: {result['original_ats_score']}% → Optimized: {result['optimized_ats_score']}%")
        print("Saved to ats_optimized.json")