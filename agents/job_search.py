import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

APP_ID  = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")
COUNTRY = "in"

# ── ChromaDB setup ────────────────────────────────────────────────────────────
import chromadb
from chromadb.config import Settings

chroma_client = chromadb.PersistentClient(path="./chroma_db")
jobs_collection = chroma_client.get_or_create_collection(
    name="adzuna_jobs",
    metadata={"description": "Real-time jobs from Adzuna"}
)


def fetch_jobs(role: str, location: str = "India", count: int = 20) -> list:
    """Fetch jobs from Adzuna and index in ChromaDB."""
    print(f"[Agent 6] Fetching jobs: {role} | {location}")
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    try:
        r = requests.get(url, params={
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "what": role,
            "where": location,
            "results_per_page": count,
            "sort_by": "date"
        }, timeout=15)

        print(f"[Agent 6] Status: {r.status_code}")
        if r.status_code != 200:
            print(f"[Agent 6] Error: {r.text[:200]}")
            return []

        jobs = []
        for idx, job in enumerate(r.json().get("results", [])[:count]):
            sal_min = job.get("salary_min")
            sal_max = job.get("salary_max")
            salary = f"₹{int(sal_min):,}–₹{int(sal_max):,}" if sal_min and sal_max else "Not disclosed"

            job_id = f"{role}_{location}_{idx}_{job.get('id', idx)}"
            job_text = f"{job.get('title', '')} {job.get('description', '')}"

            jobs.append({
                "job_id":   job_id,
                "title":    job.get("title", "N/A"),
                "company":  job.get("company", {}).get("display_name", "N/A"),
                "location": job.get("location", {}).get("display_name", location),
                "salary":   salary,
                "source":   "Adzuna",
                "link":     job.get("redirect_url", "N/A"),
                "description": job.get("description", "")[:500]
            })

            # Index in ChromaDB
            try:
                jobs_collection.upsert(
                    ids=[job_id],
                    documents=[job_text],
                    metadatas=[{
                        "role": role,
                        "title": job.get("title", ""),
                        "company": job.get("company", {}).get("display_name", ""),
                        "location": location
                    }]
                )
            except Exception as e:
                print(f"[Agent 6] ChromaDB index warning: {e}")

        print(f"[Agent 6] Found {len(jobs)} jobs, indexed in ChromaDB")
        return jobs

    except Exception as e:
        print(f"[Agent 6] Failed: {e}")
        return []


def search_similar_jobs(query: str, role: str, top_k: int = 5) -> list:
    """RAG: retrieve jobs similar to query from ChromaDB."""
    try:
        results = jobs_collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"role": role}
        )
        ids = results.get("ids", [[]])[0]
        return ids
    except Exception as e:
        print(f"[Agent 6] RAG search failed: {e}")
        return []


def run_job_search(career_goal_result: dict, location: str = "India", count: int = 20) -> dict:
    role = career_goal_result.get("normalized_role", "data analyst")
    jobs = fetch_jobs(role, location, count)

    if not jobs:
        print("[Agent 6] No results — using fallback")
        jobs = _fallback_jobs(role)

    # ── Save to SQLite ───────────────────────────────────────────
    try:
        from db import save_jobs
        user_id = os.getenv("USER_ID", "default_user")
        save_jobs(user_id, role, location, jobs)
        print(f"[Agent 6] Saved to SQLite for user: {user_id}")
    except Exception as e:
        print(f"[Agent 6] DB save skipped: {e}")
    # ────────────────────────────────────────────────────────────

    return {"role": role, "location": location, "total_found": len(jobs), "jobs": jobs}


def _fallback_jobs(role: str) -> list:
    return [
        {"job_id": "fallback_1", "title": f"{role.title()} Fresher", "company": "AI Startup India", "location": "Bangalore", "salary": "6-8 LPA", "source": "Fallback", "link": "https://internshala.com", "description": ""},
        {"job_id": "fallback_2", "title": f"Junior {role.title()}", "company": "TCS Digital",        "location": "Hyderabad", "salary": "4-6 LPA", "source": "Fallback", "link": "https://internshala.com", "description": ""},
    ]


if __name__ == "__main__":
    with open("career_goal_analysis.json") as f:
        career_goal_result = json.load(f)

    result = run_job_search(career_goal_result)

    print(f"\n{'='*50}\nJOBS — {result['role'].upper()}\n{'='*50}")
    for i, j in enumerate(result["jobs"], 1):
        print(f"\n{i}. {j['title']} @ {j['company']}")
        print(f"   {j['location']} | {j['salary']}")
        print(f"   {j['link']}")

    with open("job_listings.json", "w") as f:
        json.dump(result, f, indent=2)
    print("\nSaved to job_listings.json")
