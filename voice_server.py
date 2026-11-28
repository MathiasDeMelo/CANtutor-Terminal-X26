# voice_server.py
"""
CANtutor VoiceOS integration: an MCP server (stdio) that VoiceOS launches.
Bridge: speech -> tool call -> Flask planner -> speakable text.
All prerequisite logic lives in Flask; this file only formats the answer for speech.
"""
import os
import sys

import requests
from mcp.server.fastmcp import FastMCP

FLASK_URL = os.environ.get("FLASK_URL", "http://localhost:5000").rstrip("/")
USE_STUB = os.environ.get("USE_STUB", "1") == "1"
TIMEOUT = 10

mcp = FastMCP("cantutor")

STUDENT = {"grade": None, "completed": [], "interests": ""}


def log(*args):
    print(*args, file=sys.stderr, flush=True)  # never stdout: stdio transport


def call_flask(path: str, payload: dict):
    """POST to Flask. Returns (data, error_sentence); exactly one is None."""
    url = f"{FLASK_URL}{path}"
    try:
        r = requests.post(url, json=payload, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        log("Flask unreachable:", url)
        return None, "Sorry, I can't reach the planner right now. Please check that the backend is running."
    except requests.exceptions.Timeout:
        return None, "The planner is taking too long to respond. Please try again."
    try:
        data = r.json()
    except ValueError:
        log("Non-JSON response:", r.status_code, r.text[:200])
        return None, "The planner sent back something I couldn't understand."
    if r.status_code >= 400:
        log("Flask error:", r.status_code, data)
        msg = data.get("error") if isinstance(data, dict) else None
        return None, msg or "The planner couldn't handle that request."
    return data, None


def join_words(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def describe_impact(impact, names=None):
    """Turn Flask's impact list (strings or dicts) into a list of short phrases."""
    names = names or {}
    bits = []
    for item in impact:
        if isinstance(item, str):
            bits.append(item)
        elif isinstance(item, dict):
            label = item.get("name") or names.get(item.get("code")) or item.get("code") or "a course"
            reason = item.get("reason") or item.get("message") or item.get("status")
            bits.append(f"{label} ({reason})" if reason else label)
    return bits


def summarize(data: dict) -> str:
    """Turn Flask's roadmap into a few plain spoken sentences (used by plan_courses)."""
    # Use a spoken_summary if Flask ever adds one.
    if data.get("spoken_summary"):
        return data["spoken_summary"]

    roadmap = data.get("roadmap") or []
    if not roadmap:
        return "I couldn't find any courses for that pathway yet."

    names = {c.get("code"): c.get("name", c.get("code")) for c in roadmap}
    sentences = []

    for grade in sorted({c.get("grade") for c in roadmap if c.get("grade") is not None}):
        parts = []
        for c in (c for c in roadmap if c.get("grade") == grade):
            name = c.get("name", c.get("code", "a course"))
            status = c.get("status", "")
            if status == "completed":
                continue
            elif status == "eligible":
                parts.append(f"{name}, which you can take now")
            else:
                reqs = [names.get(code, code) for code in c.get("requires", [])]
                if reqs:
                    parts.append(f"{name}, once you've finished {join_words(reqs)}")
                else:
                    parts.append(name)
        if parts:
            sentences.append(f"In Grade {grade}: {join_words(parts)}.")

    # If Flask includes impact on a plan response, mention it too.
    bits = describe_impact(data.get("impact") or [], names)
    if bits:
        sentences.append(f"This change affects {join_words(bits)}.")
    return " ".join(sentences)


def summarize_impact(data: dict, change: str, course: str) -> str:
    """Short spoken answer for what-if: impact first, no full roadmap re-read."""
    if data.get("spoken_summary"):
        return data["spoken_summary"]

    roadmap = data.get("roadmap") or []
    names = {c.get("code"): c.get("name", c.get("code")) for c in roadmap}

    bits = describe_impact(data.get("impact") or [], names)
    if not bits:
        return f"Good news: choosing to {change} {course} doesn't affect any of your later courses."
    return f"If you {change} {course}, this affects {join_words(bits)}."


def student_is_known() -> bool:
    return STUDENT["grade"] is not None


@mcp.tool()
def plan_courses(grade: int, completed_courses: list[str], interests: str = "") -> str:
    """Build a Grade 10-12 course roadmap for a high school student.
    Use when the student says what grade they are in, which courses they have
    completed, and what they are interested in (for example computer science).
    completed_courses can be empty. interests can be empty if undecided."""
    if grade not in (10, 11, 12):
        return "I can plan for Grades 10, 11, and 12. Which grade are you in?"

    STUDENT.update(grade=grade, completed=list(completed_courses or []), interests=interests or "")

    if USE_STUB:
        return ("In Grade 10: Computing Foundations, which you can take now. "
                "In Grade 11: Programming, once you've finished Computing Foundations. "
                "In Grade 12: Advanced Computing, once you've finished Programming.")

    data, err = call_flask("/api/plan", {
        "grade": STUDENT["grade"],
        "completed": STUDENT["completed"],
        "interests": STUDENT["interests"],
    })
    return err or summarize(data)


@mcp.tool()
def what_if(change: str, course: str, replace_with: str = "") -> str:
    """Explain what would change in the student's roadmap if they add, swap,
    or skip a course. Use for follow-ups after a roadmap was given, such as
    'What if I skip Programming?'
    change must be exactly one of: 'add', 'skip', 'swap'.
    course is the course being added, skipped, or swapped out.
    replace_with is only for 'swap': the course to take instead."""
    change = (change or "").strip().lower()

    if not student_is_known():
        return "I need to know a bit about you first. Tell me your grade, completed courses, and interests."
    if change not in ("add", "skip", "swap"):
        return "I can handle adding, skipping, or swapping a course. Which would you like?"
    if not course:
        return "Which course are you asking about?"
    if change == "swap" and not replace_with:
        return f"What would you like to take instead of {course}?"

    if USE_STUB:
        return f"If you {change} {course}, this affects Advanced Computing (it requires Programming)."

    # NOTE: request shape for /api/what-if is a guess until Flask confirms it.
    data, err = call_flask("/api/what-if", {
        "grade": STUDENT["grade"],
        "completed": STUDENT["completed"],
        "interests": STUDENT["interests"],
        "change": change,
        "course": course,
        "replace_with": replace_with,
    })
    return err or summarize_impact(data, change, course)


@mcp.tool()
def mark_course_completed(course: str) -> str:
    """Record that the student has completed another course, for example
    'I also finished Computing Foundations'."""
    if not student_is_known():
        return "Tell me your grade and courses first, then I can update them."
    if course and course not in STUDENT["completed"]:
        STUDENT["completed"].append(course)
    return f"Got it. I've noted that you completed {course}."


if __name__ == "__main__":
    log(f"cantutor MCP server starting (stub={USE_STUB}, flask={FLASK_URL})")
    mcp.run(transport="stdio")