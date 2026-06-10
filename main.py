"""
main.py — CareerPilot AI
Usage:
  Full pipeline : python main.py "resume.pdf" "I want to become an AI Engineer"
  API server    : uvicorn main:app --reload
"""

import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from agents.interview_coach import recruiter_respond as ask_interviewer

app = FastAPI(title="CareerPilot AI", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


@app.post("/api/mock-interview")
async def mock_interview(request: Request):
    body = await request.json()
    feedback = ask_interviewer(
        user_answer=body["answer"],
        question=body["question"],
        role=body["role"],
        history=body.get("history", [])
    )
    return {"feedback": feedback}


if __name__ == "__main__":
    from graph.pipeline import run_pipeline
    if len(sys.argv) < 3:
        print('Usage: python main.py "resume.pdf" "I want to become an AI Engineer"')
        sys.exit(1)
    run_pipeline(sys.argv[1], sys.argv[2])