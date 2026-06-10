"""
agents/skill_gap.py — Agent 3
Skill gap analysis with live YouTube videos, learning roadmap,
and personalized project suggestions.
"""

import os
import json
import re
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

SKILL_PRIORITY = {
    "TensorFlow":        {"priority": "high",   "weeks": 3, "type": "framework", "difficulty": "medium", "prereq": ["Python"]},
    "PyTorch":           {"priority": "high",   "weeks": 3, "type": "framework", "difficulty": "medium", "prereq": ["Python"]},
    "Docker":            {"priority": "high",   "weeks": 2, "type": "devops",    "difficulty": "easy",   "prereq": ["Linux"]},
    "AWS":               {"priority": "medium", "weeks": 4, "type": "cloud",     "difficulty": "hard",   "prereq": ["Linux"]},
    "Kubernetes":        {"priority": "medium", "weeks": 3, "type": "devops",    "difficulty": "hard",   "prereq": ["Docker"]},
    "LangChain":         {"priority": "high",   "weeks": 2, "type": "llm",       "difficulty": "medium", "prereq": ["Python", "LLMs"]},
    "LangGraph":         {"priority": "medium", "weeks": 2, "type": "llm",       "difficulty": "medium", "prereq": ["LangChain"]},
    "FastAPI":           {"priority": "high",   "weeks": 1, "type": "framework", "difficulty": "easy",   "prereq": ["Python"]},
    "Scikit-learn":      {"priority": "high",   "weeks": 2, "type": "ml",        "difficulty": "easy",   "prereq": ["Python"]},
    "Pandas":            {"priority": "high",   "weeks": 1, "type": "data",      "difficulty": "easy",   "prereq": ["Python"]},
    "NumPy":             {"priority": "high",   "weeks": 1, "type": "data",      "difficulty": "easy",   "prereq": ["Python"]},
    "Tableau":           {"priority": "medium", "weeks": 2, "type": "viz",       "difficulty": "easy",   "prereq": []},
    "Power BI":          {"priority": "medium", "weeks": 2, "type": "viz",       "difficulty": "easy",   "prereq": ["Excel"]},
    "Statistics":        {"priority": "high",   "weeks": 3, "type": "theory",    "difficulty": "medium", "prereq": []},
    "Excel":             {"priority": "low",    "weeks": 1, "type": "tool",      "difficulty": "easy",   "prereq": []},
    "Spark":             {"priority": "low",    "weeks": 3, "type": "data",      "difficulty": "hard",   "prereq": ["Python", "SQL"]},
    "Hugging Face":      {"priority": "high",   "weeks": 2, "type": "llm",       "difficulty": "medium", "prereq": ["Python", "Transformers"]},
    "Fine-tuning":       {"priority": "medium", "weeks": 2, "type": "llm",       "difficulty": "hard",   "prereq": ["PyTorch", "Hugging Face"]},
    "CI/CD":             {"priority": "medium", "weeks": 2, "type": "devops",    "difficulty": "medium", "prereq": ["Git", "Docker"]},
    "Linux":             {"priority": "medium", "weeks": 1, "type": "devops",    "difficulty": "easy",   "prereq": []},
    "Deep Learning":     {"priority": "high",   "weeks": 4, "type": "ml",        "difficulty": "hard",   "prereq": ["Python", "Machine Learning"]},
    "RAG":               {"priority": "high",   "weeks": 2, "type": "llm",       "difficulty": "medium", "prereq": ["LangChain", "Vector Databases"]},
    "Vector Databases":  {"priority": "high",   "weeks": 1, "type": "llm",       "difficulty": "easy",   "prereq": ["Python"]},
    "MLOps":             {"priority": "medium", "weeks": 3, "type": "devops",    "difficulty": "hard",   "prereq": ["Docker", "AWS"]},
    "React":             {"priority": "high",   "weeks": 3, "type": "frontend",  "difficulty": "medium", "prereq": ["JavaScript", "HTML", "CSS"]},
    "Node.js":           {"priority": "high",   "weeks": 3, "type": "backend",   "difficulty": "medium", "prereq": ["JavaScript"]},
    "SQL":               {"priority": "high",   "weeks": 2, "type": "data",      "difficulty": "easy",   "prereq": []},
    "HTML":              {"priority": "high",   "weeks": 1, "type": "frontend",  "difficulty": "easy",   "prereq": []},
    "CSS":               {"priority": "high",   "weeks": 1, "type": "frontend",  "difficulty": "easy",   "prereq": ["HTML"]},
    "REST APIs":         {"priority": "high",   "weeks": 1, "type": "backend",   "difficulty": "easy",   "prereq": []},
    "TypeScript":        {"priority": "medium", "weeks": 2, "type": "frontend",  "difficulty": "medium", "prereq": ["JavaScript"]},
    "MongoDB":           {"priority": "medium", "weeks": 2, "type": "database",  "difficulty": "easy",   "prereq": []},
    "PostgreSQL":        {"priority": "medium", "weeks": 2, "type": "database",  "difficulty": "easy",   "prereq": ["SQL"]},
}

# ── Static docs + practice links ──────────────────────────────────────────────
STATIC_RESOURCES = {
    "TensorFlow":      {"practice": "https://www.hackerrank.com/domains/ai",                          "docs": "https://www.tensorflow.org/tutorials", "course": "https://www.coursera.org/specializations/tensorflow-in-practice"},
    "PyTorch":         {"practice": "https://www.kaggle.com/learn",                                   "docs": "https://pytorch.org/tutorials",         "course": "https://www.coursera.org/learn/deep-neural-networks-with-pytorch"},
    "Docker":          {"practice": "https://labs.play-with-docker.com",                              "docs": "https://docs.docker.com/get-started",  "course": "https://www.udemy.com/course/docker-mastery/"},
    "AWS":             {"practice": "https://aws.amazon.com/free",                                    "docs": "https://aws.amazon.com/getting-started","course": "https://aws.amazon.com/training/classroom/"},
    "Kubernetes":      {"practice": "https://killercoda.com/playgrounds/scenario/kubernetes",         "docs": "https://kubernetes.io/docs/tutorials",  "course": "https://www.coursera.org/specializations/kubernetes"},
    "LangChain":       {"practice": None,                                                             "docs": "https://python.langchain.com/docs/get_started/introduction", "course": "https://www.deeplearning.ai/short-courses/langchain-for-llm-application-development/"},
    "LangGraph":       {"practice": None,                                                             "docs": "https://langchain-ai.github.io/langgraph", "course": "https://www.deeplearning.ai/short-courses/ai-agents-in-langgraph/"},
    "FastAPI":         {"practice": "https://www.hackerrank.com/domains/python",                      "docs": "https://fastapi.tiangolo.com/tutorial", "course": "https://www.udemy.com/course/rest-api-flask-and-python/"},
    "Scikit-learn":    {"practice": "https://www.kaggle.com/learn/intro-to-machine-learning",         "docs": "https://scikit-learn.org/stable/tutorial", "course": "https://www.coursera.org/learn/machine-learning-with-python"},
    "Pandas":          {"practice": "https://www.kaggle.com/learn/pandas",                            "docs": "https://pandas.pydata.org/docs/getting_started", "course": "https://www.kaggle.com/learn/pandas"},
    "NumPy":           {"practice": "https://www.hackerrank.com/domains/python",                      "docs": "https://numpy.org/doc/stable/user/quickstart.html", "course": "https://www.udemy.com/course/python-for-data-science-and-machine-learning-bootcamp/"},
    "SQL":             {"practice": "https://www.hackerrank.com/domains/sql",                         "docs": "https://www.w3schools.com/sql",         "course": "https://www.coursera.org/specializations/learn-sql-basics-data-science"},
    "Deep Learning":   {"practice": "https://www.kaggle.com/learn/intro-to-deep-learning",            "docs": "https://d2l.ai",                        "course": "https://www.coursera.org/specializations/deep-learning"},
    "RAG":             {"practice": None,                                                             "docs": "https://python.langchain.com/docs/use_cases/question_answering", "course": "https://www.deeplearning.ai/short-courses/building-evaluating-advanced-rag/"},
    "Vector Databases":{"practice": None,                                                             "docs": "https://docs.trychroma.com",            "course": "https://www.deeplearning.ai/short-courses/vector-databases-embeddings-applications/"},
    "Hugging Face":    {"practice": "https://huggingface.co/learn/nlp-course",                        "docs": "https://huggingface.co/docs/transformers", "course": "https://huggingface.co/learn/nlp-course"},
    "Statistics":      {"practice": "https://www.hackerrank.com/domains/statistics",                  "docs": "https://www.khanacademy.org/math/statistics-probability", "course": "https://www.khanacademy.org/math/statistics-probability"},
    "React":           {"practice": "https://www.hackerrank.com/domains/react",                       "docs": "https://react.dev/learn",               "course": "https://www.coursera.org/learn/react-basics"},
    "Node.js":         {"practice": "https://www.hackerrank.com/domains/javascript",                  "docs": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs", "course": "https://www.coursera.org/learn/server-side-nodejs"},
    "HTML":            {"practice": "https://www.hackerrank.com/domains/html",                        "docs": "https://developer.mozilla.org/en-US/docs/Learn/HTML", "course": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"},
    "CSS":             {"practice": "https://www.hackerrank.com/domains/css",                         "docs": "https://developer.mozilla.org/en-US/docs/Learn/CSS", "course": "https://www.freecodecamp.org/learn/2022/responsive-web-design/"},
    "REST APIs":       {"practice": "https://www.hackerrank.com/domains/rest-api",                    "docs": "https://restfulapi.net",                "course": "https://www.udemy.com/course/rest-api/"},
    "MongoDB":         {"practice": "https://learn.mongodb.com",                                      "docs": "https://www.mongodb.com/docs/manual/tutorial", "course": "https://learn.mongodb.com/learning-paths/"},
    "Power BI":        {"practice": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "docs": "https://learn.microsoft.com/en-us/power-bi/fundamentals/desktop-getting-started", "course": "https://learn.microsoft.com/en-us/training/powerplatform/power-bi"},
    "Tableau":         {"practice": "https://public.tableau.com",                                     "docs": "https://help.tableau.com/current/guides/get-started-tutorial/en-us/get-started-tutorial-home.htm", "course": "https://www.coursera.org/learn/data-visualization-tableau"},
    "MLOps":           {"practice": "https://www.kaggle.com/learn",                                   "docs": "https://ml-ops.org",                     "course": "https://www.coursera.org/specializations/mlops"},
}

# ── Project suggestions per skill ─────────────────────────────────────────────
SKILL_PROJECTS = {
    "TensorFlow":         "Build an image classifier on CIFAR-10 with transfer learning (MobileNetV2)",
    "PyTorch":            "Train a text generator on a public book corpus, save and load the model",
    "Docker":             "Containerize your CareerPilot AI app, push to Docker Hub, deploy to Railway/Render",
    "AWS":                "Deploy a FastAPI app on EC2 + S3 for model storage + CloudWatch for monitoring",
    "Kubernetes":         "Set up a K8s cluster locally with minikube, deploy 3 microservices",
    "LangChain":          "Build a PDF Q&A chatbot using LangChain + OpenAI + FAISS",
    "LangGraph":          "Create a multi-agent research assistant with LangGraph stateful workflows",
    "FastAPI":            "Build a REST API for your resume parser, add JWT auth + rate limiting",
    "Scikit-learn":       "Train a fraud detection model on Kaggle's Credit Card dataset, evaluate with F1",
    "Pandas":             "Analyze 1M+ row dataset (NYC Taxi), build data cleaning pipeline + insights notebook",
    "NumPy":              "Implement matrix operations from scratch, benchmark vs NumPy",
    "SQL":                "Solve 50 LeetCode SQL problems + build analytics queries on Chinook DB",
    "Deep Learning":      "Train a sentiment classifier on IMDB, achieve >90% accuracy, deploy as API",
    "RAG":                "Build a doc Q&A system: scrape 100 docs → embed → store in ChromaDB → query with LLM",
    "Vector Databases":   "Build a semantic search engine for movie plots using ChromaDB + sentence-transformers",
    "Hugging Face":       "Fine-tune BERT on a custom NER dataset, push to HF Hub",
    "Statistics":         "Complete A/B testing case study, write report with hypothesis testing",
    "React":              "Build a dashboard with 5+ components, hooks, routing, and state management",
    "Node.js":            "Build a real-time chat app with Socket.io + Express + MongoDB",
    "HTML":               "Build a 5-page responsive portfolio site from scratch",
    "CSS":                "Recreate 3 popular websites (Apple, Airbnb, Stripe) with pure CSS",
    "REST APIs":          "Build a Twitter clone API with auth, posts, comments, likes",
    "MongoDB":            "Design schema for e-commerce app, implement CRUD + aggregation pipelines",
    "Power BI":           "Build executive dashboard on Superstore dataset with DAX measures",
    "Tableau":            "Create interactive sales dashboard with maps, filters, and parameters",
    "MLOps":              "Add MLflow tracking + model registry to an existing ML project, deploy with BentoML",
}


# ── YouTube API: faster with parallel + retry ─────────────────────────────────

def fetch_youtube_videos(skill: str, max_results: int = 2) -> list:
    """Fetch top YouTube videos for a skill using YouTube Data API v3."""
    if not YOUTUBE_API_KEY:
        return _fallback_video(skill)

    query = f"{skill} full course tutorial for beginners"
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": max_results,
        "order": "relevance",
        "videoDuration": "long",
        "relevanceLanguage": "en",
        "key": YOUTUBE_API_KEY
    }

    # Try with shorter timeout + 1 retry
    for attempt in range(2):
        try:
            resp = requests.get(url, params=params, timeout=5)
            resp.raise_for_status()
            data = resp.json()

            videos = []
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                videos.append({
                    "title": snippet["title"],
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "channel": snippet["channelTitle"],
                    "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url")
                })
            return videos if videos else _fallback_video(skill)
        except Exception as e:
            if attempt == 0:
                time.sleep(0.5)  # quick retry
                continue
            print(f"[Agent 3] YouTube fetch failed for '{skill}': {e}")
            return _fallback_video(skill)
    return _fallback_video(skill)


def _fallback_video(skill: str) -> list:
    return [{
        "title": f"{skill} Full Course for Beginners",
        "url": f"https://www.youtube.com/results?search_query={skill.replace(' ', '+')}+full+course+tutorial",
        "channel": "YouTube Search",
        "thumbnail": None
    }]


def safe_json(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
    if match:
        text = match.group(1).strip()
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        text = match.group(0)
    return json.loads(text)

def generate_roadmap(missing_skills: list, matched_skills: list, role: str) -> dict:
    # Limit skills to avoid token overflow
    missing_skills = missing_skills[:6]
    
    prompt = f"""Create a learning roadmap JSON for a {role} role.
Learn: {', '.join(missing_skills)}
Already know: {', '.join(matched_skills[:5])}

Respond ONLY with valid JSON, no markdown, no comments:
{{"total_months": 3, "months": [{{"month": 1, "theme": "Foundations", "skills": ["skill1"], "goal": "Learn basics", "build": "small project"}}, {{"month": 2, "theme": "Intermediate", "skills": ["skill2"], "goal": "Build something", "build": "real project"}}, {{"month": 3, "theme": "Advanced", "skills": ["skill3"], "goal": "Ship it", "build": "portfolio project"}}], "quick_wins": ["skill1"]}}"""

    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1, max_tokens=600
            )
            return safe_json(r.choices[0].message.content)
        except Exception as e:
            if attempt == 2:
                print(f"[Agent 3] Roadmap generation failed: {e}")
                return {"total_months": 1, "months": [{"month": 1, "theme": "Learning", "skills": missing_skills, "goal": "Learn required skills", "build": "Portfolio project"}], "quick_wins": []}
            time.sleep(1)


def categorize_gaps(missing_skills: list) -> dict:
    high, medium, low, unknown = [], [], [], []
    for skill in missing_skills:
        info = SKILL_PRIORITY.get(skill)
        if info:
            {"high": high, "medium": medium, "low": low}[info["priority"]].append(skill)
        else:
            unknown.append(skill)
    return {"high": high, "medium": medium, "low": low, "other": unknown}


def get_resources_parallel(missing_skills: list) -> dict:
    """Fetch YouTube videos in parallel — way faster than sequential."""
    resources = {}

    def fetch_one(skill):
        return skill, fetch_youtube_videos(skill, max_results=2)

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_one, skill): skill for skill in missing_skills}
        for future in as_completed(futures):
            try:
                skill, videos = future.result()
                static = STATIC_RESOURCES.get(skill, {})
                project = SKILL_PROJECTS.get(skill, f"Build a small project using {skill} and document it on GitHub")
                priority_info = SKILL_PRIORITY.get(skill, {})

                resources[skill] = {
                    "priority": priority_info.get("priority", "medium"),
                    "weeks": priority_info.get("weeks", 2),
                    "difficulty": priority_info.get("difficulty", "medium"),
                    "prereq": priority_info.get("prereq", []),
                    "youtube": videos,
                    "practice": static.get("practice"),
                    "docs": static.get("docs", f"https://www.google.com/search?q={skill.replace(' ', '+')}+official+documentation"),
                    "course": static.get("course"),
                    "project_idea": project
                }
            except Exception as e:
                print(f"[Agent 3] Resource fetch error: {e}")
    return resources


def run_skill_gap_agent(career_goal_result: dict) -> dict:
    role = career_goal_result["normalized_role"]
    missing_skills = career_goal_result["missing_skills"]
    matched_skills = career_goal_result["matched_skills"]
    match_score = career_goal_result["match_score"]

    print(f"[Agent 3] Analyzing {len(missing_skills)} skill gaps for {role}")

    gap_categories = categorize_gaps(missing_skills)

    print("[Agent 3] Fetching resources in parallel...")
    resources = get_resources_parallel(missing_skills)

    print("[Agent 3] Generating learning roadmap...")
    roadmap_data = generate_roadmap(missing_skills, matched_skills, role)

    if match_score >= 70:
        readiness = "Job Ready — apply now and learn remaining skills in parallel"
    elif match_score >= 50:
        readiness = "Almost Ready — 1-2 months of focused learning needed"
    elif match_score >= 30:
        readiness = "In Progress — 3-4 months of learning needed"
    else:
        readiness = "Early Stage — 6+ months of structured learning needed"

    # Calculate total effort
    total_weeks = sum(SKILL_PRIORITY.get(s, {}).get("weeks", 2) for s in missing_skills)

    result = {
        "role": role,
        "match_score": match_score,
        "readiness": readiness,
        "total_gaps": len(missing_skills),
        "missing_skills": missing_skills,
        "matched_skills": matched_skills,
        "gap_categories": gap_categories,
        "total_estimated_weeks": total_weeks,
        "resources": resources,
        "roadmap": roadmap_data,
    }

    # ── Save to SQLite ───────────────────────────────────────────
    try:
        from db import get_conn
        user_id = os.getenv("USER_ID", "default_user")
        conn = get_conn()
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS skill_gaps (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,
                total_gaps INTEGER,
                high_priority INTEGER,
                medium_priority INTEGER,
                low_priority INTEGER,
                total_weeks INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            INSERT INTO skill_gaps (user_id, role, total_gaps, high_priority, medium_priority, low_priority, total_weeks)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, role, len(missing_skills),
            len(gap_categories["high"]), len(gap_categories["medium"]), len(gap_categories["low"]),
            total_weeks
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[Agent 3] DB save warning: {e}")
    # ────────────────────────────────────────────────────────────

    print(f"[Agent 3] Readiness: {readiness}")
    print(f"[Agent 3] Roadmap generated: {roadmap_data.get('total_months', '?')} months")
    return result


if __name__ == "__main__":
    with open("career_goal_analysis.json") as f:
        career_goal_result = json.load(f)

    result = run_skill_gap_agent(career_goal_result)

    print("\n" + "="*55)
    print(f"  Role      : {result['role'].upper()}")
    print(f"  Readiness : {result['readiness']}")
    print(f"  Gaps      : {result['total_gaps']} skills")
    print(f"  Est. weeks: {result['total_estimated_weeks']}")
    print(f"  High priority: {len(result['gap_categories']['high'])}")
    print(f"  Medium: {len(result['gap_categories']['medium'])}")
    print(f"  Low: {len(result['gap_categories']['low'])}")

    print("\n  LEARNING ROADMAP:")
    for month in result["roadmap"].get("months", []):
        print(f"\n  Month {month['month']} — {month['theme']}")
        print(f"  Skills : {', '.join(month['skills'])}")
        print(f"  Goal   : {month['goal']}")
        print(f"  Build  : {month['build']}")

    print("\n  RESOURCES (with project ideas):")
    for skill, res in result["resources"].items():
        print(f"\n  📌 {skill}  [{res['priority'].upper()} | ~{res['weeks']}w | {res['difficulty']}]")
        if res.get("prereq"):
            print(f"     Prereq: {', '.join(res['prereq'])}")
        for v in res.get("youtube", []):
            print(f"     ▶ {v['title']} — {v['channel']}")
            print(f"       {v['url']}")
        if res.get("course"):
            print(f"     🎓 Course: {res['course']}")
        if res.get("docs"):
            print(f"     📖 Docs: {res['docs']}")
        if res.get("practice"):
            print(f"     🏋 Practice: {res['practice']}")
        if res.get("project_idea"):
            print(f"     🛠 Build  : {res['project_idea']}")

    with open("skill_gap_analysis.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to skill_gap_analysis.json")
