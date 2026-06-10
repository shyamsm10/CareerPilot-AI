"""
agents/interview_coach.py — Agent 9
Professional AI recruiter mock interview with:
- Groq-generated ideal answers for each question
- Detailed post-answer recommendations
- End-of-interview skill gap analysis linked to Agent 2
- History-aware feedback
"""

import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

RECRUITER_SYSTEM = """You are Sarah Chen, a senior technical recruiter with 12 years at top tech firms (Google, Meta, Stripe).
You conduct realistic, professional mock interviews.

Rules:
- Ask ONE question at a time — never multiple
- After candidate answers: give 2-3 sentence honest feedback (what was strong, what was missing), then ask the next question
- Use STAR method prompts if an answer lacks structure ("Can you walk me through a specific situation where...")
- Escalate naturally: start with HR/background → behavioral → technical → role-specific deep dives
- Reference their actual projects/skills when asking technical questions
- Be warm but rigorous — real stakes, real feedback
- After 8 questions, give a 4-5 sentence overall assessment with 2 specific improvement areas
- Never break character. Never list multiple questions at once."""


def safe_json(text):
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    for pattern in [r'```(?:json)?(.*?)```', r'\{.*\}']:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1 if '```' in pattern else 0).strip())
            except json.JSONDecodeError:
                continue
    raise ValueError("No valid JSON found in response")


def generate_questions(profile: dict, career_goal_result: dict) -> dict:
    role = career_goal_result.get("normalized_role", "software engineer")
    matched_skills = ", ".join(career_goal_result.get("matched_skills", [])[:8])
    missing_skills = ", ".join(career_goal_result.get("missing_skills", [])[:4])
    projects = profile.get("projects", [])[:3]
    project_details = "; ".join([
        f"{p.get('name','')}: {p.get('description','')[:80]}" for p in projects
    ])
    name = profile.get("name", "Candidate")
    exp = profile.get("experience", [])
    exp_summary = "; ".join([f"{e.get('role', e.get('title',''))} at {e.get('company','')}" for e in exp[:2]])

    prompt = f"""Generate a structured interview question bank for {name} applying for {role}.

Candidate profile:
- Skills: {matched_skills}
- Skill gaps: {missing_skills}
- Projects: {project_details}
- Experience: {exp_summary or 'fresher/student'}

Return ONLY valid JSON:
{{
  "hr_questions": [
    {{"question": "...", "ideal_answer": "2-3 sentence model answer", "key_points": ["point1", "point2"], "what_they_look_for": "...", "red_flags": "..."}}
  ],
  "behavioral_questions": [
    {{"question": "...", "ideal_answer": "STAR-formatted example answer", "key_points": ["Situation", "Task", "Action", "Result"], "star_prompt": "...", "strong_answer_includes": "..."}}
  ],
  "technical_questions": [
    {{"question": "...", "ideal_answer": "comprehensive technical answer", "key_points": ["concept1", "concept2"], "difficulty": "medium", "key_concepts": "...", "model_answer": "..."}}
  ],
  "project_questions": [
    {{"question": "...", "ideal_answer": "detailed walkthrough of how to answer", "key_points": ["architecture", "challenges", "impact"], "probing_followup": "..."}}
  ]
}}

Generate: 4 HR, 4 behavioral (STAR-based), 6 technical (role-specific, escalating difficulty), 3 project questions about their actual projects.
For each question, provide a realistic ideal_answer and 3-5 key_points the candidate should hit."""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Return only valid compact JSON. No markdown, no explanation."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=3500
    )
    return safe_json(r.choices[0].message.content)


def recruiter_respond(user_answer: str, question: str, role: str, history: list, q_number: int = 1, total: int = 13) -> str:
    context = f"This is question {q_number} of {total}. "
    if q_number >= total:
        context += "This is the final question. After evaluating, give an overall interview assessment."

    messages = [{"role": "system", "content": RECRUITER_SYSTEM}]
    if history:
        messages += history[-8:]

    messages.append({
        "role": "user",
        "content": f"{context}\nQuestion asked: {question}\nCandidate's answer: {user_answer}"
    })

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.55,
        max_tokens=400
    )
    return r.choices[0].message.content.strip()


def evaluate_answer_detailed(user_answer: str, question: str, ideal_answer: str,
                             key_points: list, question_type: str, role: str) -> dict:
    prompt = f"""You are Sarah Chen, a senior technical recruiter evaluating a candidate's answer.

Question Type: {question_type}
Role: {role}

Question: {question}

Ideal Answer: {ideal_answer}
Key points that should be covered: {', '.join(key_points)}

Candidate's answer: {user_answer}

Evaluate honestly and return ONLY valid JSON (no markdown):
{{
  "score": 75,
  "verdict": "strong | adequate | weak",
  "what_was_strong": "1-2 sentences on what they did well",
  "what_was_missing": "1-2 sentences on key points/concepts they missed",
  "ideal_answer_summary": "The ideal answer rewritten concisely (2-3 sentences)",
  "how_to_improve": "3 specific actionable steps to improve this answer",
  "followup_suggestion": "One follow-up question they should be ready for"
}}"""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert interview evaluator. Return only valid JSON, no markdown fences."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=600
    )
    return safe_json(r.choices[0].message.content)


# ── NEW: Generate final recommendations tied to skill gaps ────────────────────

def generate_final_recommendations(session_log: list, scores: list,
                                   career_goal_result: dict, profile: dict) -> dict:
    """
    After interview ends: link weak answers to specific skill gaps.
    Tells candidate exactly which skills to focus on based on their performance.
    """
    role = career_goal_result.get("normalized_role", "Software Engineer")
    target_role = career_goal_result.get("career_goal", role)
    missing_skills = career_goal_result.get("missing_skills", [])
    matched_skills = career_goal_result.get("matched_skills", [])

    # Find weak answers (score < 60)
    weak_answers = [entry for entry in session_log if entry.get("score", 100) < 60 and entry.get("answer") != "[skipped]"]
    strong_answers = [entry for entry in session_log if entry.get("score", 0) >= 75]

    # Identify question types where they struggled
    weak_types = [entry["type"] for entry in weak_answers]
    type_counts = {}
    for t in weak_types:
        type_counts[t] = type_counts.get(t, 0) + 1
    weakest_type = max(type_counts, key=type_counts.get) if type_counts else "None"

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Build context for LLM
    weak_summary = "\n".join([
        f"- {e['type']}: {e['q'][:80]} (scored {e['score']}/100)"
        for e in weak_answers[:5]
    ]) or "No weak answers — great job!"

    strong_summary = "\n".join([
        f"- {e['type']}: {e['q'][:80]} (scored {e['score']}/100)"
        for e in strong_answers[:3]
    ]) or "Need more practice on all question types."

    prompt = f"""You are Sarah Chen giving final post-interview feedback to a {role} candidate.

INTERVIEW PERFORMANCE:
- Average Score: {avg_score}/100
- Weakest Area: {weakest_type}
- Total Questions: {len(session_log)}

WEAK ANSWERS (need improvement):
{weak_summary}

STRONG ANSWERS (keep doing this):
{strong_summary}

CANDIDATE'S SKILL PROFILE:
- Skills they have: {', '.join(matched_skills)}
- Skills they're missing for {target_role}: {', '.join(missing_skills)}

Now give them a structured "what to do next" plan. Return ONLY valid JSON (no markdown):
{{
  "overall_verdict": "hired | strong_maybe | needs_work | not_ready",
  "readiness_score": 72,
  "performance_summary": "2-3 sentence honest summary of their performance",
  "top_3_improvements": [
    {{
      "area": "specific area (e.g. 'System Design for ML systems')",
      "why": "why this matters for {role}",
      "action": "specific 1-week action they can take (e.g. 'Build a small RAG system end-to-end and document trade-offs')",
      "linked_skill_gap": "which of their missing skills this addresses"
    }}
  ],
  "weak_areas_to_practice": ["area1", "area2", "area3"],
  "strong_areas_to_leverage": ["area1", "area2"],
  "interview_readiness_for_role": "ready_now | 2_weeks | 1_month | 3_months",
  "next_steps": [
    "1. Specific action (with timeline)",
    "2. Specific action (with timeline)",
    "3. Specific action (with timeline)"
  ],
  "motivational_close": "1 encouraging sentence"
}}

Be specific to {role} interviews. Link recommendations to their actual missing_skills: {', '.join(missing_skills[:5])}."""

    r = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a senior career coach. Return only valid JSON, no markdown fences."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4,
        max_tokens=1000
    )
    return safe_json(r.choices[0].message.content)


def print_final_recommendations(rec: dict, role: str, avg_score: float):
    """Pretty-print the end-of-interview recommendations."""
    print(f"\n{'═'*62}")
    print(f"  📋 FINAL REPORT — {role.upper()}")
    print(f"{'═'*62}\n")

    print(f"  🎯 Overall Verdict : {rec.get('overall_verdict', '').upper().replace('_', ' ')}")
    print(f"  📊 Readiness Score : {rec.get('readiness_score', avg_score)}/100")
    print(f"  ⏰ Time to Ready   : {rec.get('interview_readiness_for_role', '').replace('_', ' ')}")
    print(f"\n  💬 Summary:\n     {rec.get('performance_summary', '')}")

    print(f"\n  🔧 TOP 3 IMPROVEMENTS:\n")
    for i, imp in enumerate(rec.get('top_3_improvements', []), 1):
        print(f"     {i}. {imp.get('area', '')}")
        print(f"        Why    : {imp.get('why', '')}")
        print(f"        Action : {imp.get('action', '')}")
        print(f"        Skill  : → {imp.get('linked_skill_gap', '')}")
        print()

    weak = rec.get('weak_areas_to_practice', [])
    strong = rec.get('strong_areas_to_leverage', [])
    if weak:
        print(f"  ⚠️  Practice these : {', '.join(weak)}")
    if strong:
        print(f"  ✅ You're strong at: {', '.join(strong)}")

    print(f"\n  📅 NEXT STEPS:\n")
    for step in rec.get('next_steps', []):
        print(f"     {step}")

    print(f"\n  💪 {rec.get('motivational_close', '')}")
    print(f"\n{'═'*62}\n")


def run_interview_coach(profile: dict, career_goal_result: dict) -> dict:
    role = career_goal_result.get("normalized_role", "role")
    print(f"\n[Agent 9] Generating personalized question bank with ideal answers for {role}...")
    questions = generate_questions(profile, career_goal_result)

    counts = {k: len(v) for k, v in questions.items() if isinstance(v, list)}
    print(f"[Agent 9] Question bank ready: {counts}")

    questions["_meta"] = {
        "role": role,
        "name": profile.get("name", "Candidate")
    }

    try:
        from db import save_interview
        user_id = os.getenv("USER_ID", "default_user")
        save_interview(user_id, role, [{"type": "bank_generated", "questions": counts}], "")
        print(f"[Agent 9] Saved question bank to SQLite for user: {user_id}")
    except Exception as e:
        print(f"[Agent 9] DB save skipped: {e}")

    return questions


# ── CLI Mock Interview ─────────────────────────────────────────────────────────

def flatten_questions(questions: dict) -> list:
    flow = []
    for q in questions.get("hr_questions", []):
        flow.append({
            "type": "HR", "q": q["question"],
            "hint": q.get("what_they_look_for", ""),
            "ideal": q.get("ideal_answer", ""),
            "key_points": q.get("key_points", [])
        })
    for q in questions.get("behavioral_questions", []):
        flow.append({
            "type": "Behavioral", "q": q["question"],
            "hint": q.get("star_prompt", ""),
            "strong": q.get("strong_answer_includes", ""),
            "ideal": q.get("ideal_answer", ""),
            "key_points": q.get("key_points", [])
        })
    for q in questions.get("project_questions", []):
        flow.append({
            "type": "Project", "q": q["question"],
            "followup": q.get("probing_followup", ""),
            "ideal": q.get("ideal_answer", ""),
            "key_points": q.get("key_points", [])
        })
    for q in questions.get("technical_questions", []):
        flow.append({
            "type": "Technical", "q": q["question"],
            "difficulty": q.get("difficulty", "medium"),
            "hint": q.get("key_concepts", ""),
            "model": q.get("model_answer", ""),
            "ideal": q.get("ideal_answer", ""),
            "key_points": q.get("key_points", [])
        })
    return flow


def print_divider(char="─", width=62):
    print(char * width)


def print_feedback_box(eval_result: dict, question_type: str):
    print(f"\n  ┌─── Detailed Feedback [{question_type}] ───┐")
    print(f"  │  Score : {eval_result.get('score', 0)}/100 ({eval_result.get('verdict', '').upper()})")
    print(f"  │")
    print(f"  │  ✅ Strong:")
    print(f"  │     {eval_result.get('what_was_strong', '')}")
    print(f"  │")
    print(f"  │  ❌ Missing:")
    print(f"  │     {eval_result.get('what_was_missing', '')}")
    print(f"  │")
    print(f"  │  💡 Ideal Answer:")
    print(f"  │     {eval_result.get('ideal_answer_summary', '')}")
    print(f"  │")
    print(f"  │  📈 How to Improve:")
    for step in eval_result.get('how_to_improve', '').split('\n'):
        if step.strip():
            print(f"  │     • {step.strip()}")
    print(f"  │")
    print(f"  │  🔮 Be ready for follow-up:")
    print(f"  │     {eval_result.get('followup_suggestion', '')}")
    print(f"  └{'─'*48}┘\n")


def mock_interview_cli(questions: dict, career_goal_result: dict = None, profile: dict = None):
    role = questions.get("_meta", {}).get("role", "Software Engineer")
    name = questions.get("_meta", {}).get("name", "Candidate")
    flow = flatten_questions(questions)
    total = len(flow)

    print(f"\n{'═'*62}")
    print(f"  CareerPilot AI — Mock Interview")
    print(f"  Role: {role}  |  Candidate: {name}")
    print(f"  Interviewer: Sarah Chen (Senior Technical Recruiter)")
    print(f"{'═'*62}")
    print(f"\n  {total} questions across HR, Behavioral, Project & Technical.")
    print(f"  Commands:  answer · ideal · hint · skip · history · quit\n")
    print_divider()

    history = []
    session_log = []
    scores = []

    for i, item in enumerate(flow, 1):
        diff = f" [{item.get('difficulty','').upper()}]" if item.get("difficulty") else ""
        print(f"\n  [{item['type']}{diff}  ·  Q{i}/{total}]")
        print(f"\n  ❓ {item['q']}\n")

        while True:
            try:
                user_input = input("  You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Interview ended. Good luck!")
                _save_session(session_log, role, name, scores, career_goal_result)
                return

            if not user_input:
                continue

            cmd = user_input.lower()

            if cmd == "quit":
                print("\n  Ending interview...")
                _save_session(session_log, role, name, scores, career_goal_result)
                return

            if cmd == "skip":
                print("  ⏭  Skipped.\n")
                session_log.append({
                    "q": item["q"], "type": item["type"],
                    "answer": "[skipped]", "feedback": "", "score": 0
                })
                scores.append(0)
                break

            if cmd == "hint":
                hint = item.get("hint") or item.get("strong") or "Think about a concrete example from your experience."
                print(f"\n  💡 {hint}\n")
                continue

            if cmd == "ideal":
                print(f"\n  📖 Ideal Answer:")
                print(f"     {item.get('ideal', 'Not available')}")
                print(f"\n  Key points to cover:")
                for pt in item.get('key_points', []):
                    print(f"     • {pt}")
                print()
                continue

            if cmd == "history":
                if not session_log:
                    print("  No answers yet.\n")
                else:
                    print("\n  ── Session so far ──")
                    for idx, entry in enumerate(session_log, 1):
                        score_str = f" [{entry.get('score', 0)}/100]" if entry.get('score', 0) > 0 else ""
                        print(f"  Q{idx} [{entry['type']}]{score_str}: {entry['q'][:60]}...")
                        if entry['answer'] != "[skipped]":
                            print(f"  You: {entry['answer'][:80]}...")
                        print()
                continue

            # Real answer
            print("\n  Sarah Chen:\n")
            feedback = recruiter_respond(user_input, item["q"], role, history, i, total)
            for line in feedback.split("\n"):
                print(f"  {line}")
            print()

            print("  ⏳ Generating detailed feedback...\n")
            eval_result = evaluate_answer_detailed(
                user_answer=user_input,
                question=item["q"],
                ideal_answer=item.get("ideal", ""),
                key_points=item.get("key_points", []),
                question_type=item["type"],
                role=role
            )

            print_feedback_box(eval_result, item["type"])

            history.append({"role": "user", "content": f"Q: {item['q']}\nA: {user_input}"})
            history.append({"role": "assistant", "content": feedback})

            score = eval_result.get("score", 0)
            scores.append(score)
            session_log.append({
                "q": item["q"],
                "type": item["type"],
                "answer": user_input,
                "verbal_feedback": feedback,
                "detailed_feedback": eval_result,
                "score": score
            })
            print_divider()
            break

    # ── Final summary + recommendations ──
    print(f"\n{'═'*62}")
    print("  ✅ Interview complete!")
    print(f"{'═'*62}\n")
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    print(f"  📊 Average Score: {avg_score}/100")
    if scores:
        print(f"  📈 Highest: {max(scores)}/100  |  Lowest: {min(scores)}/100")

    # ── NEW: Generate final recommendations if we have career_goal_result ──
    if career_goal_result and session_log:
        print("\n  ⏳ Generating personalized improvement plan based on your performance + skill gaps...\n")
        try:
            recommendations = generate_final_recommendations(
                session_log=session_log,
                scores=scores,
                career_goal_result=career_goal_result,
                profile=profile or {}
            )
            print_final_recommendations(recommendations, role, avg_score)
            _save_session(session_log, role, name, scores, career_goal_result, recommendations)
            return
        except Exception as e:
            print(f"  ⚠️  Could not generate recommendations: {e}")

    _save_session(session_log, role, name, scores, career_goal_result)


def _save_session(log: list, role: str, name: str, scores: list = None,
                  career_goal_result: dict = None, final_recommendations: dict = None):
    if not log:
        return
    filename = f"interview_session_{name.lower().replace(' ','_')}.json"
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    payload = {
        "role": role,
        "candidate": name,
        "average_score": avg_score,
        "session": log,
        "final_recommendations": final_recommendations
    }
    with open(filename, "w") as f:
        json.dump(payload, f, indent=2)
    print(f"  📄 Session saved to {filename}\n")

    try:
        from db import save_interview
        user_id = os.getenv("USER_ID", "default_user")
        assessment = f"Average score: {avg_score}/100"
        if final_recommendations:
            assessment += f" | Verdict: {final_recommendations.get('overall_verdict', '')}"
            assessment += f" | Readiness: {final_recommendations.get('interview_readiness_for_role', '')}"
        save_interview(user_id, role, log, assessment)
        print(f"  💾 Session also saved to SQLite for user: {user_id}")
    except Exception as e:
        print(f"  ⚠️  SQLite save skipped: {e}")


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    with open("parsed_resume.json") as f:
        profile = json.load(f)
    with open("career_goal_analysis.json") as f:
        career_goal_result = json.load(f)

    result = run_interview_coach(profile, career_goal_result)

    with open("interview_questions.json", "w") as f:
        json.dump(result, f, indent=2)
    print("Saved to interview_questions.json")

    ans = input("\nStart mock interview? (y/n): ").strip().lower()
    if ans == "y":
        mock_interview_cli(result, career_goal_result=career_goal_result, profile=profile)
