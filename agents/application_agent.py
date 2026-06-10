"""
agents/application_agent.py — Agent 8
Generates a personalized cover letter for the top ranked job.
"""

import os
import json
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_cover_letter(job: dict, profile: dict, career_goal_result: dict) -> str:
    name = profile.get("name", "Candidate")
    skills = ", ".join(career_goal_result.get("matched_skills", [])[:4])
    project = profile.get("projects", [{}])[0].get("name", "my AI project")

    prompt = f"""Write a 3-paragraph cover letter (max 150 words) for {name} applying to {job.get('title')} at {job.get('company')}.
Skills: {skills}. Key project: {project}.
Para 1: Why this role. Para 2: One skill + one project. Para 3: Call to action.
Return only the letter text."""

    for attempt in range(3):
        try:
            r = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=250
            )
            return r.choices[0].message.content.strip()
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                print(f"[Agent 8] Rate limited, waiting 15s...")
                time.sleep(15)
            else:
                return f"Cover letter generation failed: {e}"


def run_application_agent(ranked_jobs: dict, profile: dict, career_goal_result: dict) -> dict:
    # Only top 1 recommended job to avoid TPM limits
    top_jobs = [j for j in ranked_jobs.get("ranked_jobs", []) if j.get("recommended")][:1]
    if not top_jobs:
        top_jobs = ranked_jobs.get("ranked_jobs", [])[:1]

    print(f"[Agent 8] Generating cover letter for top job...")

    cover_letters = {}
    for job in top_jobs:
        key = f"{job['title']} at {job['company']}"
        print(f"[Agent 8] Writing: {key}")
        cover_letters[key] = {
            "job": job,
            "cover_letter": generate_cover_letter(job, profile, career_goal_result)
        }

    print(f"[Agent 8] Done — {len(cover_letters)} cover letter generated")
    return {"cover_letters": cover_letters, "total": len(cover_letters)}


if __name__ == "__main__":
    with open("ranked_jobs.json") as f:
        ranked_jobs = json.load(f)
    with open("parsed_resume.json") as f:
        profile = json.load(f)
    with open("career_goal_analysis.json") as f:
        career_goal_result = json.load(f)

    result = run_application_agent(ranked_jobs, profile, career_goal_result)

    for key, data in result["cover_letters"].items():
        print(f"\n--- {key} ---\n{data['cover_letter']}\n")

    with open("cover_letters.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Saved to cover_letters.json")
