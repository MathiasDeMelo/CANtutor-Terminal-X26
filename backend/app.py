"""Flask API for the course planner."""

from flask import Flask, request

from .roadmap import build_roadmap
from .what_if import compare_roadmaps

app = Flask(__name__)


def is_course_list(value):
    return isinstance(value, list) and all(
        isinstance(code, str) and code.strip() for code in value
    )


def normalize_codes(codes):
    return {code.strip().upper() for code in codes}


@app.post("/api/plan")
def plan():
    profile = request.get_json(silent=True)
    if not isinstance(profile, dict):
        return {"error": "Send a JSON object with grade, completed, and interests."}, 400

    grade = profile.get("grade")
    completed = profile.get("completed")
    interests = profile.get("interests")

    if type(grade) is not int or grade not in range(9, 13):
        return {"error": "grade must be an integer from 9 to 12."}, 400
    if not is_course_list(completed):
        return {"error": "completed must be an array of course codes."}, 400
    if not isinstance(interests, str) or not interests.strip():
        return {"error": "interests must be a non-empty string."}, 400

    completed_codes = normalize_codes(completed)
    interest = interests.strip().casefold()
    if "planned" not in profile and "previous_planned" not in profile:
        return {"roadmap": build_roadmap(grade, completed_codes, interest), "impact": []}

    planned = profile.get("planned")
    previous_planned = profile.get("previous_planned", [])
    if not is_course_list(planned):
        return {"error": "planned must be an array of course codes."}, 400
    if not is_course_list(previous_planned):
        return {"error": "previous_planned must be an array of course codes."}, 400

    revised = build_roadmap(grade, completed_codes, interest, normalize_codes(planned))
    previous = build_roadmap(
        grade, completed_codes, interest, normalize_codes(previous_planned)
    )
    return {"roadmap": revised, "impact": compare_roadmaps(previous, revised)}
