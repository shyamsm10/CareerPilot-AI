"""
api/routes.py — FastAPI endpoints for CareerPilot AI
"""

import os
import json
import shutil
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from graph.pipeline import run_pipeline

router = APIRouter()
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/analyze")
async def analyze(
    resume: UploadFile = File(...),
    career_goal: str = Form(...)
):
    """Main endpoint — runs full 9-agent pipeline."""
    if not resume.filename.endswith((".pdf", ".docx")):
        raise HTTPException(400, "Only PDF or DOCX files supported.")

    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, resume.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(resume.file, f)

    try:
        result = run_pipeline(file_path, career_goal)

        if result.get("error"):
            raise HTTPException(500, result["error"])

        return JSONResponse({
            "status": "success",
            "profile": result["parsed_profile"],
            "goal_analysis": result["goal_analysis"],
            "skill_gap": result["skill_gap_analysis"],
            "ats": result["ats_result"],
            "jobs": result["ranked_jobs"],
            "cover_letters": result["cover_letters"],
            "interview_questions": result["interview_questions"],
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/results/{data_type}")
async def get_results(data_type: str):
    """Get saved results by type."""
    file_map = {
        "profile": "parsed_resume.json",
        "goal": "career_goal_analysis.json",
        "skills": "skill_gap_analysis.json",
        "ats": "ats_optimized.json",
        "resume": "generated_resume.json",
        "jobs": "ranked_jobs.json",
        "covers": "cover_letters.json",
        "interview": "interview_questions.json",
    }

    if data_type not in file_map:
        raise HTTPException(404, f"Unknown type. Choose: {list(file_map.keys())}")

    path = file_map[data_type]
    if not os.path.exists(path):
        raise HTTPException(404, "No data found. Run /analyze first.")

    with open(path) as f:
        return json.load(f)


@router.get("/health")
async def health():
    return {"status": "ok", "agents": 9}