import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ── Target role profiles (RAG seed data) ──────────────────────────────────────

ROLE_PROFILES = {
    "ai engineer": {
        "required_skills": [
            "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "LLMs", "RAG", "LangChain", "Vector Databases", "FastAPI",
            "Docker", "AWS", "Git", "MLOps", "Model Deployment"
        ],
        "good_to_have": [
            "LangGraph", "Kubernetes", "Hugging Face", "Fine-tuning",
            "Prompt Engineering", "CI/CD", "Linux"
        ],
        "description": "Builds and deploys AI/ML models and LLM-powered applications at scale.",
        "avg_salary_india": "6-15 LPA",
        "top_companies": ["Google", "Microsoft", "Infosys", "TCS", "Wipro", "Startups"]
    },
    "ml engineer": {
        "required_skills": [
            "Python", "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Scikit-learn", "Docker", "AWS", "Git", "MLOps",
            "Model Evaluation", "Data Pipelines", "SQL"
        ],
        "good_to_have": [
            "Kubernetes", "Apache Spark", "Airflow", "Feature Stores",
            "A/B Testing", "Model Monitoring"
        ],
        "description": "Focuses on building, training, and deploying production ML models.",
        "avg_salary_india": "6-14 LPA",
        "top_companies": ["Amazon", "Flipkart", "Ola", "Swiggy", "Zomato", "Startups"]
    },
    "data scientist": {
        "required_skills": [
            "Python", "SQL", "Machine Learning", "Statistics", "Data Analysis",
            "Pandas", "NumPy", "Scikit-learn", "Data Visualisation",
            "Tableau", "Power BI", "Jupyter"
        ],
        "good_to_have": [
            "Deep Learning", "NLP", "R", "Spark", "Hadoop",
            "Storytelling with Data", "Business Acumen"
        ],
        "description": "Extracts insights from data to drive business decisions.",
        "avg_salary_india": "5-12 LPA",
        "top_companies": ["Accenture", "Deloitte", "EY", "KPMG", "Amazon", "Google"]
    },
    "data analyst": {
        "required_skills": [
            "SQL", "Excel", "Python", "Data Visualisation", "Tableau",
            "Power BI", "Statistics", "Reporting", "Business Analysis"
        ],
        "good_to_have": [
            "Machine Learning", "Google Analytics", "Looker",
            "ETL", "Stakeholder Communication"
        ],
        "description": "Analyses data and builds dashboards to support business decisions.",
        "avg_salary_india": "4-9 LPA",
        "top_companies": ["Deloitte", "EY", "Capgemini", "Cognizant", "TCS"]
    },
    "nlp engineer": {
        "required_skills": [
            "Python", "NLP", "Deep Learning", "Transformers", "Hugging Face",
            "BERT", "GPT", "Text Classification", "Named Entity Recognition",
            "Machine Learning", "PyTorch"
        ],
        "good_to_have": [
            "LangChain", "RAG", "Vector Databases", "Multilingual NLP",
            "Speech Processing", "Fine-tuning LLMs"
        ],
        "description": "Builds systems that understand and generate human language.",
        "avg_salary_india": "7-16 LPA",
        "top_companies": ["Google", "Microsoft", "Amazon", "AI Startups"]
    },
    "full stack developer": {
        "required_skills": [
            "JavaScript", "React", "Node.js", "Python", "HTML", "CSS",
            "SQL", "REST APIs", "Git", "Docker"
        ],
        "good_to_have": [
            "TypeScript", "Next.js", "AWS", "MongoDB", "PostgreSQL",
            "CI/CD", "Testing Frameworks"
        ],
        "description": "Builds end-to-end web applications — frontend and backend.",
        "avg_salary_india": "5-12 LPA",
        "top_companies": ["Infosys", "Wipro", "TCS", "Startups", "Product Companies"]
    }
}


def normalize_goal(goal: str) -> str:
    goal_lower = goal.lower().strip()
    for role_key in ROLE_PROFILES:
        if role_key in goal_lower:
            return role_key
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "You map a user's career goal to one of these roles: "
                           "ai engineer, ml engineer, data scientist, data analyst, nlp engineer, full stack developer. "
                           "Return ONLY the role name, nothing else."
            },
            {"role": "user", "content": f"My career goal: {goal}"}
        ],
        temperature=0.1,
        max_tokens=20
    )
    return response.choices[0].message.content.strip().lower()


def extract_skills_from_projects(profile: dict) -> list:
    projects = profile.get("projects", [])
    if not projects:
        return []

    project_text = ""
    for p in projects:
        project_text += f"- {p.get('name', '')}: {p.get('description', '')} | Tech: {', '.join(p.get('technologies', p.get('tech_stack', [])))}\n"

    if not project_text.strip():
        return []

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": "Extract technical skills from project descriptions. Return ONLY a JSON array of skill names, nothing else. Example: [\"LLMs\", \"RAG\", \"FastAPI\"]"
            },
            {
                "role": "user",
                "content": f"Extract all technical skills from these projects:\n{project_text}"
            }
        ],
        temperature=0.1,
        max_tokens=300
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        skills = json.loads(raw)
        return skills if isinstance(skills, list) else []
    except Exception:
        return []


def llm_skill_match(current_skills: list, required: list, good_to_have: list) -> dict:
    match_prompt = f"""
You are a technical skill matcher. Compare the user's skills against required and good-to-have skills.

User's current skills: {', '.join(current_skills)}

Required skills to evaluate: {', '.join(required)}
Good-to-have skills to evaluate: {', '.join(good_to_have)}

Rules:
- If the user has a skill that means the same thing or covers the concept, count it as matched.
- Be generous but honest — if they clearly have the concept, mark it matched
- "bonus_matched" must only contain skills from the good_to_have list

Return ONLY this JSON, no explanation, no markdown:
{{"matched": ["skill1", "skill2"], "missing": ["skill3", "skill4"], "bonus_matched": ["skill5"]}}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a skill matcher. Return only valid JSON, nothing else."},
            {"role": "user", "content": match_prompt}
        ],
        temperature=0.1,
        max_tokens=500
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    data = json.loads(raw)
    return {
        "matched": data.get("matched", []),
        "missing": data.get("missing", []),
        "bonus_matched": data.get("bonus_matched", [])
    }


def analyze_career_goal(profile: dict, career_goal: str) -> dict:
    normalized_role = normalize_goal(career_goal)
    role_data = ROLE_PROFILES.get(normalized_role, ROLE_PROFILES["ai engineer"])

    skills = profile.get("skills", {})
    current_skills = (
        skills.get("programming_languages", []) +
        skills.get("frameworks", []) +
        skills.get("tools", []) +
        skills.get("databases", []) +
        skills.get("cloud", []) +
        skills.get("other", [])
    )

    print("[Agent 2] Extracting skills from projects...")
    project_skills = extract_skills_from_projects(profile)
    all_skills = list(set(current_skills + project_skills))
    print(f"[Agent 2] Total skills (resume + projects): {len(all_skills)}")

    required = role_data["required_skills"]
    good_to_have = role_data["good_to_have"]

    print("[Agent 2] Running LLM skill matcher...")
    match_data = llm_skill_match(all_skills, required, good_to_have)
    matched = match_data["matched"]
    missing = match_data["missing"]
    bonus_matched = match_data["bonus_matched"]

    match_score = round((len(matched) / len(required)) * 100, 1)

    prompt = f"""
You are a career coach. A fresher has the following profile and wants to become a {normalized_role}.

Their current skills: {', '.join(all_skills)}
Their projects: {', '.join([p['name'] for p in profile.get('projects', [])])}
Their experience: {profile.get('experience', [{}])[0].get('title', 'fresher') if profile.get('experience') else 'No experience'}

Skills they already have: {', '.join(matched)}
Skills they are missing: {', '.join(missing)}

Write a SHORT 3-sentence personalized career assessment:
1. What they are good at (based on their actual profile)
2. The most important skill gaps to fill
3. One encouraging sentence about their chances

Return only the 3 sentences, no headers, no bullet points.
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a helpful, honest career coach."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        max_tokens=300
    )

    assessment = response.choices[0].message.content.strip()

    return {
        "career_goal": career_goal,
        "normalized_role": normalized_role,
        "role_description": role_data["description"],
        "avg_salary": role_data["avg_salary_india"],
        "top_companies": role_data["top_companies"],
        "required_skills": required,
        "good_to_have_skills": good_to_have,
        "matched_skills": matched,
        "missing_skills": missing,
        "bonus_skills": bonus_matched,
        "match_score": match_score,
        "personalized_assessment": assessment
    }


def run_career_goal_agent(profile: dict, career_goal: str) -> dict:
    print(f"[Agent 2] Analyzing career goal: '{career_goal}'")
    result = analyze_career_goal(profile, career_goal)
    print(f"[Agent 2] Role matched: {result['normalized_role']}")
    print(f"[Agent 2] Skill match score: {result['match_score']}%")
    print(f"[Agent 2] Missing skills: {', '.join(result['missing_skills'])}")

    # ── Save to SQLite ───────────────────────────────────────────
    try:
        from db import save_career_goal
        user_id = os.getenv("USER_ID", "default_user")
        db_payload = {
            "target_role": result["normalized_role"],
            "strengths": result["matched_skills"],
            "gaps": result["missing_skills"],
            "roadmap": result["personalized_assessment"]
        }
        save_career_goal(user_id, db_payload)
        print(f"[Agent 2] Saved to SQLite for user: {user_id}")
    except Exception as e:
        print(f"[Agent 2] DB save skipped: {e}")
    # ────────────────────────────────────────────────────────────

    return result


if __name__ == "__main__":
    with open("parsed_resume.json", "r") as f:
        profile = json.load(f)

    career_goal = input("Enter your career goal (e.g. 'I want to become an AI Engineer'): ")

    result = run_career_goal_agent(profile, career_goal)

    print("\n" + "="*50)
    print("CAREER GOAL ANALYSIS:")
    print("="*50)
    print(f"Target Role     : {result['normalized_role'].upper()}")
    print(f"Match Score     : {result['match_score']}%")
    print(f"Avg Salary      : {result['avg_salary']}")
    print(f"\nSkills You Have : {', '.join(result['matched_skills'])}")
    print(f"\nMissing Skills  : {', '.join(result['missing_skills'])}")
    print(f"\nBonus Skills    : {', '.join(result['bonus_skills'])}")
    print(f"\nAssessment:\n{result['personalized_assessment']}")

    with open("career_goal_analysis.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to career_goal_analysis.json")

