# db.py — Database setup
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "careerpilot.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Create tables on first run."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            experience TEXT,
            projects TEXT,
            education TEXT,
            raw_text TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS career_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            target_role TEXT,
            strengths TEXT,
            gaps TEXT,
            roadmap TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS interview_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            history TEXT,
            final_assessment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            location TEXT,
            results TEXT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def save_resume(user_id, parsed):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO resumes (user_id, name, email, phone, skills, experience, projects, education, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        parsed.get("name", ""),
        parsed.get("email", ""),
        parsed.get("phone", ""),
        json.dumps(parsed.get("skills", [])),
        json.dumps(parsed.get("experience", [])),
        json.dumps(parsed.get("projects", [])),
        json.dumps(parsed.get("education", [])),
        parsed.get("raw_text", "")
    ))
    conn.commit()
    conn.close()

def save_career_goal(user_id, result):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO career_goals (user_id, target_role, strengths, gaps, roadmap)
        VALUES (?, ?, ?, ?, ?)
    """, (
        user_id,
        result.get("target_role", ""),
        json.dumps(result.get("strengths", [])),
        json.dumps(result.get("gaps", [])),
        result.get("roadmap", "")
    ))
    conn.commit()
    conn.close()

def save_interview(user_id, role, history, assessment=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO interview_sessions (user_id, role, history, final_assessment)
        VALUES (?, ?, ?, ?)
    """, (user_id, role, json.dumps(history), assessment))
    conn.commit()
    conn.close()

def save_jobs(user_id, role, location, results):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO jobs (user_id, role, location, results)
        VALUES (?, ?, ?, ?)
    """, (user_id, role, location, json.dumps(results)))
    conn.commit()
    conn.close()

def get_interview_history(user_id, limit=10):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT id, role, history, final_assessment, created_at
        FROM interview_sessions
        WHERE user_id = ?
        ORDER BY created_at DESC
        LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return [
        {
            "id": r[0],
            "role": r[1],
            "history": json.loads(r[2]),
            "assessment": r[3],
            "created_at": r[4]
        } for r in rows
    ]

def get_latest_resume(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT * FROM resumes WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row[0], "user_id": row[1], "name": row[2],
        "email": row[3], "phone": row[4],
        "skills": json.loads(row[5] or "[]"),
        "experience": json.loads(row[6] or "[]"),
        "projects": json.loads(row[7] or "[]"),
        "education": json.loads(row[8] or "[]"),
        "raw_text": row[9], "created_at": row[10]
    }
def get_latest_career_goal(user_id):
    """Fetch the most recent career goal analysis for a user."""
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT target_role, strengths, gaps, roadmap
        FROM career_goals
        WHERE user_id = ?
        ORDER BY created_at DESC LIMIT 1
    """, (user_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "target_role": row[0],
        "strengths": json.loads(row[1] or "[]"),
        "gaps": json.loads(row[2] or "[]"),
        "roadmap": row[3]
    }
# Add this to db.py
def get_skill_gaps_history(user_id, limit=5):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        SELECT role, total_gaps, high_priority, medium_priority, low_priority, total_weeks, created_at
        FROM skill_gaps
        WHERE user_id = ?
        ORDER BY created_at DESC LIMIT ?
    """, (user_id, limit))
    rows = c.fetchall()
    conn.close()
    return rows
