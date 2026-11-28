# mock_flask.py: fake planner so you can test voice_server.py with USE_STUB=0
from flask import Flask, jsonify, request

app = Flask(__name__)

ROADMAP = [
    {"grade": 10, "code": "DEMO10", "name": "Computing Foundations", "status": "eligible", "requires": []},
    {"grade": 11, "code": "DEMO11", "name": "Programming", "status": "conditional", "requires": ["DEMO10"]},
    {"grade": 12, "code": "DEMO12", "name": "Advanced Computing", "status": "conditional", "requires": ["DEMO11"]},
]

@app.post("/api/plan")
def plan():
    body = request.get_json(silent=True) or {}
    if body.get("grade") not in (10, 11, 12):
        return jsonify(error="Grade must be 10, 11, or 12."), 400
    return jsonify(roadmap=ROADMAP, impact=[])

@app.post("/api/what-if")
def what_if():
    body = request.get_json(silent=True) or {}
    impact = []
    if body.get("change") == "skip" and "programming" in (body.get("course") or "").lower():
        impact = [{"name": "Advanced Computing", "reason": "it requires Programming"}]
    return jsonify(roadmap=ROADMAP, impact=impact)

if __name__ == "__main__":
    app.run(port=5000)