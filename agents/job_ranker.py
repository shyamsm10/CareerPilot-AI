"""
agents/job_ranker.py — Agent 7
RAG-based job ranker using ChromaDB + Groq LLM.
Falls back to heuristic scoring if RAG is unavailable.
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── ChromaDB setup ────────────────────────────────────────────────────────────
try:
    import chromadb
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    jobs_collection = chroma_client.get_or_create_collection("adzuna_jobs")
    RAG_ENABLED = True
    print("[Agent 7] ChromaDB RAG enabled")
except Exception as e:
    RAG_ENABLED = False
    print(f"[Agent 7] ChromaDB unavailable, using heuristic only: {e}")


# ── Heuristic scoring (fallback) ──────────────────────────────────────────────

def score_job_heuristic(job: dict, matched_skills: list, missing_skills: list) -> dict:
    title = job.get("title", "").lower()
    description = job.get("description", "").lower()
    combined_text = title + " " + description

    skill_hits = sum(1 for s in matched_skills if s.lower() in combined_text)
    skill_score = min((skill_hits / max(len(matched_skills), 1)) * 100, 100)

    fresher_keywords = ["fresher", "junior", "entry", "trainee", "graduate", "0-2", "0-1"]
    senior_keywords = ["senior", "lead", "manager", "head", "principal", "5+", "7+"]
    if any(k in combined_text for k in fresher_keywords):
        level_score = 100
    elif any(k in combined_text for k in senior_keywords):
        level_score = 20
    else:
        level_score = 60

    salary_str = job.get("salary", "").lower().replace(",", "")
    salary_score = 50
    try:
        nums = re.findall(r'\d+', salary_str)
        if nums:
            avg = sum(int(n) for n in nums[:2]) / len(nums[:2])
            if avg >= 10:
                salary_score = 100
            elif avg >= 6:
                salary_score = 75
            elif avg >= 4:
                salary_score = 50
            else:
                salary_score = 25
    except Exception:
        pass

    total = round((skill_score * 0.5) + (level_score * 0.25) + (salary_score * 0.25), 1)

    return {
        **job,
        "skill_score": round(skill_score, 1),
        "level_score": round(level_score, 1),
        "salary_score": round(salary_score, 1),
        "total_score": total,
        "match_reason": f"Skill match: {skill_score:.0f}% | Level fit: {level_score:.0f}% | Salary: {salary_score:.0f}%",
        "method": "heuristic"
    }


# ── RAG-based scoring ─────────────────────────────────────────────────────────

def build_profile_query(profile: dict, career_goal: dict) -> str:
    skills = profile.get("skills", {})
    all_skills = []
    for cat in skills.values():
        if isinstance(cat, list):
            all_skills.extend(cat)
    projects = " ".join([p.get("name", "") for p in profile.get("projects", [])])
    target_role = career_goal.get("normalized_role", "")
    return f"{target_role} {' '.join(all_skills)} {projects}"


def retrieve_relevant_jobs(query: str, role: str, top_k: int) -> list:
    """ChromaDB RAG retrieval."""
    try:
        results = jobs_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"role": role}
        )
        return results.get("ids", [[]])[0]
    except Exception as e:
        print(f"[Agent 7] ChromaDB query failed: {e}")
        return []


def rank_with_llm(retrieved_jobs: list, profile: dict, career_goal: dict) -> list:
    """LLM ranks retrieved jobs with reasoning."""
    if not retrieved_jobs:
        return []

    jobs_text = "\n".join([
        f"{i+1}. {j['title']} @ {j['company']} | {j['location']} | {j['salary']}\n   {j.get('description', '')[:150]}"
        for i, j in enumerate(retrieved_jobs)
    ])

    user_skills = []
    skills = profile.get("skills", {})
    for cat in skills.values():
        if isinstance(cat, list):
            user_skills.extend(cat)

    prompt = f"""You are a job matching expert. Rank these jobs for a {career_goal.get('normalized_role', '')} candidate.

Candidate skills: {', '.join(user_skills)}
Projects: {', '.join([p.get('name', '') for p in profile.get('projects', [])])}

Jobs:
{jobs_text}

Return ONLY a JSON array (no markdown):
[
  {{"rank": 1, "job_title": "...", "company": "...", "match_score": 85, "reason": "1 sentence"}}
]
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You are a job matching expert. Return only valid JSON, no markdown."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=800
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    raw = raw.strip()

    try:
        return json.loads(raw)
    except Exception:
        return []


def score_job_rag(job: dict, similarity_distance: float, llm_rank: dict) -> dict:
    """Combine RAG similarity + LLM rank into final score."""
    # Lower distance = more similar. Convert to 0-100.
    similarity_score = max(0, 100 - (similarity_distance * 50))
    llm_score = llm_rank.get("match_score", 50) if llm_rank else 50
    final_score = round((similarity_score * 0.4) + (llm_score * 0.6), 1)

    return {
        **job,
        "similarity_score": round(similarity_score, 1),
        "llm_score": llm_score,
        "total_score": final_score,
        "match_reason": llm_rank.get("reason", f"Retrieved by RAG similarity ({similarity_score:.0f}%)"),
        "method": "rag"
    }


# ── Main entry point ──────────────────────────────────────────────────────────

def run_job_ranker(profile: dict, job_listings: dict, career_goal_result: dict, top_k: int = 5) -> dict:
    jobs = job_listings.get("jobs", [])
    matched_skills = career_goal_result.get("matched_skills", [])
    missing_skills = career_goal_result.get("missing_skills", [])
    target_role = career_goal_result.get("normalized_role", "")

    print(f"[Agent 7] Ranking {len(jobs)} jobs for role: {target_role}")

    # ── Try RAG first ──
    if RAG_ENABLED and jobs:
        try:
            query = build_profile_query(profile, career_goal_result)
            print(f"[Agent 7] RAG query: '{query[:80]}...'")

            # Retrieve top-k similar jobs
            results = jobs_collection.query(
                query_texts=[query],
                n_results=min(top_k, len(jobs)),
                where={"role": target_role}
            )

            ids = results.get("ids", [[]])[0]
            distances = results.get("distances", [[]])[0]
            job_map = {j.get("job_id", j.get("title", "") + j.get("company", "")): j for j in jobs}

            retrieved_jobs = []
            for jid, dist in zip(ids, distances):
                if jid in job_map:
                    retrieved_jobs.append((job_map[jid], dist))

            if retrieved_jobs:
                # LLM final ranking
                jobs_only = [j for j, _ in retrieved_jobs]
                llm_ranking = rank_with_llm(jobs_only, profile, career_goal_result)
                llm_map = {(r.get("job_title", "") + r.get("company", "")): r for r in llm_ranking}

                scored = []
                for job, dist in retrieved_jobs:
                    key = job.get("title", "") + job.get("company", "")
                    llm_rank = llm_map.get(key, {})
                    scored.append(score_job_rag(job, dist, llm_rank))

                scored.sort(key=lambda x: x["total_score"], reverse=True)
                for i, job in enumerate(scored):
                    job["rank"] = i + 1
                    job["recommended"] = i < 3

                print(f"[Agent 7] RAG ranking complete. Top: {scored[0]['title']} ({scored[0]['total_score']}%)")
                return {
                    "role": target_role,
                    "total_ranked": len(scored),
                    "ranked_jobs": scored,
                    "method": "rag"
                }
        except Exception as e:
            print(f"[Agent 7] RAG failed, using heuristic: {e}")

    # ── Fallback: heuristic ──
    print("[Agent 7] Using heuristic scoring")
    scored = [score_job_heuristic(job, matched_skills, missing_skills) for job in jobs]
    ranked = sorted(scored, key=lambda x: x["total_score"], reverse=True)

    for i, job in enumerate(ranked):
        job["rank"] = i + 1
        job["recommended"] = i < 3

    if ranked:
        print(f"[Agent 7] Top job: {ranked[0]['title']} at {ranked[0]['company']} (score: {ranked[0]['total_score']})")

    return {
        "role": target_role,
        "total_ranked": len(ranked),
        "ranked_jobs": ranked,
        "method": "heuristic"
    }


if __name__ == "__main__":
    with open("parsed_resume.json") as f:
        profile = json.load(f)
    with open("career_goal_analysis.json") as f:
        career_goal = json.load(f)
    with open("job_listings.json") as f:
        job_listings = json.load(f)

    result = run_job_ranker(profile, job_listings, career_goal)

    print("\n" + "="*50)
    print(f"RANKED JOBS (method: {result['method']})")
    print("="*50)
    for job in result["ranked_jobs"][:5]:
        tag = "⭐ RECOMMENDED" if job["recommended"] else ""
        print(f"\n#{job['rank']} {job['title']} — {job['company']} {tag}")
        print(f"   Score    : {job['total_score']}%")
        print(f"   Location : {job['location']}")
        print(f"   Salary   : {job['salary']}")
        print(f"   Reason   : {job['match_reason']}")
        print(f"   Link     : {job['link']}")

    with open("ranked_jobs.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to ranked_jobs.json")
