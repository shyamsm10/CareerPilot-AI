"""
graph/pipeline.py — LangGraph pipeline for all 9 agents.
"""

import os
import sys
import json
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv

load_dotenv()
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Import all agents ─────────────────────────────────────────────────────────
from agents.resume_parser import run_resume_parser
from agents.career_goal import analyze_career_goal
from agents.skill_gap import run_skill_gap_agent
from agents.ats_optimizer import run_ats_optimizer
from agents.resume_generator import run_resume_generator
from agents.job_search import run_job_search
from agents.job_ranker import run_job_ranker
from agents.application_agent import run_application_agent
from agents.interview_coach import run_interview_coach


# ── Initialize DB once ────────────────────────────────────────────────────────
try:
    from db import init_db
    init_db()
except Exception as e:
    print(f"[Pipeline] DB init warning: {e}")


# ── State definition ──────────────────────────────────────────────────────────

class CareerPilotState(TypedDict):
    resume_path: str
    career_goal: str
    parsed_profile: dict
    goal_analysis: dict
    skill_gap_analysis: dict
    ats_result: dict
    generated_resume: dict
    job_listings: dict
    ranked_jobs: dict
    cover_letters: dict
    interview_questions: dict
    error: Optional[str]
    current_step: str


# ── Agent nodes ───────────────────────────────────────────────────────────────

def node_resume_parser(state: CareerPilotState) -> CareerPilotState:
    print("\n[Pipeline] ▶ Step 1/9 — Resume Parser")
    try:
        result = run_resume_parser(state["resume_path"])
        profile = result.get("profile", result)
        print(f"[Pipeline] ✓ {profile.get('name', 'Profile loaded')}")
        return {**state, "parsed_profile": profile, "current_step": "career_goal"}
    except Exception as e:
        return {**state, "error": f"Agent 1 failed: {e}", "current_step": END}


def node_career_goal(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 2/9 — Career Goal")
    try:
        result = analyze_career_goal(state["parsed_profile"], state["career_goal"])
        print(f"[Pipeline] ✓ {result.get('normalized_role')} | {result.get('match_score')}%")
        return {**state, "goal_analysis": result, "current_step": "skill_gap"}
    except Exception as e:
        return {**state, "error": f"Agent 2 failed: {e}", "current_step": END}


def node_skill_gap(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 3/9 — Skill Gap")
    try:
        result = run_skill_gap_agent(state["goal_analysis"])
        print(f"[Pipeline] ✓ Gaps: {result.get('total_gaps')}")
        return {**state, "skill_gap_analysis": result, "current_step": "ats_optimizer"}
    except Exception as e:
        return {**state, "error": f"Agent 3 failed: {e}", "current_step": END}


def node_ats_optimizer(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 4/9 — ATS Optimizer")
    try:
        result = run_ats_optimizer(state["parsed_profile"], state["goal_analysis"])
        print(f"[Pipeline] ✓ ATS: {result.get('original_ats_score')} → {result.get('optimized_ats_score')}")
        return {**state, "ats_result": result, "current_step": "resume_generator"}
    except Exception as e:
        return {**state, "error": f"Agent 4 failed: {e}", "current_step": END}


def node_resume_generator(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 5/9 — Resume Generator")
    try:
        result = run_resume_generator(state["parsed_profile"], state["ats_result"], state["goal_analysis"])
        print("[Pipeline] ✓ Resume generated")
        return {**state, "generated_resume": result, "current_step": "job_search"}
    except Exception as e:
        return {**state, "error": f"Agent 5 failed: {e}", "current_step": END}


def node_job_search(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 6/9 — Job Search")
    try:
        result = run_job_search(state["goal_analysis"])
        print(f"[Pipeline] ✓ Jobs found: {result.get('total_found')}")
        return {**state, "job_listings": result, "current_step": "job_ranker"}
    except Exception as e:
        return {**state, "error": f"Agent 6 failed: {e}", "current_step": END}


def node_job_ranker(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 7/9 — Job Ranker")
    try:
        # New RAG version needs profile too
        result = run_job_ranker(state["parsed_profile"], state["job_listings"], state["goal_analysis"])
        print(f"[Pipeline] ✓ Ranked: {result.get('total_ranked')} jobs (method: {result.get('method')})")
        return {**state, "ranked_jobs": result, "current_step": "application_agent"}
    except Exception as e:
        return {**state, "error": f"Agent 7 failed: {e}", "current_step": END}


def node_application_agent(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 8/9 — Cover Letters")
    try:
        result = run_application_agent(state["ranked_jobs"], state["parsed_profile"], state["goal_analysis"])
        print(f"[Pipeline] ✓ Cover letters: {result.get('total')}")
        return {**state, "cover_letters": result, "current_step": "interview_coach"}
    except Exception as e:
        return {**state, "error": f"Agent 8 failed: {e}", "current_step": END}


def node_interview_coach(state: CareerPilotState) -> CareerPilotState:
    print("[Pipeline] ▶ Step 9/9 — Interview Coach")
    try:
        result = run_interview_coach(state["parsed_profile"], state["goal_analysis"])
        print("[Pipeline] ✓ Interview questions generated")
        return {**state, "interview_questions": result, "current_step": END}
    except Exception as e:
        return {**state, "error": f"Agent 9 failed: {e}", "current_step": END}


# ── Router: simple forward chain ──────────────────────────────────────────────

def router(state: CareerPilotState) -> str:
    """Route to next step or END if error."""
    if state.get("error"):
        return END
    return state.get("current_step", END)


# ── Build graph ───────────────────────────────────────────────────────────────

def build_pipeline():
    graph = StateGraph(CareerPilotState)

    # Register all nodes
    nodes = [
        ("resume_parser", node_resume_parser),
        ("career_goal", node_career_goal),
        ("skill_gap", node_skill_gap),
        ("ats_optimizer", node_ats_optimizer),
        ("resume_generator", node_resume_generator),
        ("job_search", node_job_search),
        ("job_ranker", node_job_ranker),
        ("application_agent", node_application_agent),
        ("interview_coach", node_interview_coach),
    ]
    for name, fn in nodes:
        graph.add_node(name, fn)

    # Entry point
    graph.set_entry_point("resume_parser")

    # Linear edges: each node → next node (no router needed for happy path)
    edges = [
        ("resume_parser", "career_goal"),
        ("career_goal", "skill_gap"),
        ("skill_gap", "ats_optimizer"),
        ("ats_optimizer", "resume_generator"),
        ("resume_generator", "job_search"),
        ("job_search", "job_ranker"),
        ("job_ranker", "application_agent"),
        ("application_agent", "interview_coach"),
        ("interview_coach", END),
    ]
    for src, dst in edges:
        graph.add_edge(src, dst)

    return graph.compile()


# ── Run pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(resume_path: str, career_goal: str) -> dict:
    pipeline = build_pipeline()

    initial_state: CareerPilotState = {
        "resume_path": resume_path,
        "career_goal": career_goal,
        "parsed_profile": {},
        "goal_analysis": {},
        "skill_gap_analysis": {},
        "ats_result": {},
        "generated_resume": {},
        "job_listings": {},
        "ranked_jobs": {},
        "cover_letters": {},
        "interview_questions": {},
        "error": None,
        "current_step": "resume_parser"
    }

    print("\n" + "="*55)
    print("  CareerPilot AI — Starting Full Pipeline (9 Agents)")
    print("="*55)

    final_state = pipeline.invoke(initial_state)

    print("\n" + "="*55)
    if final_state.get("error"):
        print(f"  ✗ Failed: {final_state['error']}")
    else:
        print("  ✓ All 9 agents complete!")
        _save_outputs(final_state)
        _print_summary(final_state)
    print("="*55 + "\n")

    return final_state


def _save_outputs(state):
    files = {
        "parsed_resume.json": state["parsed_profile"],
        "career_goal_analysis.json": state["goal_analysis"],
        "skill_gap_analysis.json": state["skill_gap_analysis"],
        "ats_optimized.json": state["ats_result"],
        "generated_resume.json": state["generated_resume"],
        "job_listings.json": state["job_listings"],
        "ranked_jobs.json": state["ranked_jobs"],
        "cover_letters.json": state["cover_letters"],
        "interview_questions.json": state["interview_questions"],
    }
    for fname, data in files.items():
        try:
            with open(fname, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Pipeline] Failed to save {fname}: {e}")
    print("[Pipeline] All outputs saved.")


def _print_summary(state):
    g = state["goal_analysis"]
    s = state["skill_gap_analysis"]
    a = state["ats_result"]
    j = state["ranked_jobs"]
    top = j.get("ranked_jobs", [{}])[0] if j.get("ranked_jobs") else {}
    print(f"""
  Name        : {state['parsed_profile'].get('name')}
  Target Role : {g.get('normalized_role', '').upper()}
  Match Score : {g.get('match_score')}%
  Readiness   : {s.get('readiness', 'N/A')}
  ATS Score   : {a.get('original_ats_score')} → {a.get('optimized_ats_score')}
  Jobs Found  : {state['job_listings'].get('total_found')}
  Top Job     : {top.get('title')} at {top.get('company')}
  Gaps        : {', '.join(g.get('missing_skills', []))}
""")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python graph/pipeline.py <resume_path> <career_goal>")
        print("Example: python graph/pipeline.py my_resume.pdf 'I want to become an AI Engineer'")
        sys.exit(1)

    run_pipeline(sys.argv[1], sys.argv[2])

