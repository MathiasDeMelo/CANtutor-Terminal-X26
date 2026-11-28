"""Build the Grade 10–12 plan using the eligibility checks."""

import json
from pathlib import Path

from .eligibility import meets_prerequisites

COURSES_PATH = Path(__file__).resolve().parents[1] / "data" / "computing_courses.json"
COURSES = json.loads(COURSES_PATH.read_text(encoding="utf-8"))


def build_roadmap(grade, completed, interests, planned=None):
    if interests != "computing":
        return []

    roadmap = []
    projected_credits = {}
    for code, course in sorted(COURSES.items(), key=lambda item: item[1]["grade"]):
        course_grade = course["grade"]
        if course_grade < grade or code in completed:
            continue

        required = course["requires"]
        if meets_prerequisites(required, completed):
            status = "eligible"
        elif planned is None:
            status = "conditional"
        else:
            earlier_planned = {
                credit for credit, credit_grade in projected_credits.items()
                if credit_grade < course_grade
            }
            if meets_prerequisites(required, completed | earlier_planned):
                status = "available_if_planned"
            else:
                status = "blocked"

        if planned is not None and code in planned and status != "blocked":
            projected_credits[code] = course_grade

        roadmap.append(
            {
                "grade": course_grade,
                "code": code,
                "name": course["name"],
                "status": status,
                "requires": required,
            }
        )

    return roadmap
