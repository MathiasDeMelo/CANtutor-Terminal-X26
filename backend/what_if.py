"""Compare the original and revised roadmaps and report affected courses."""


def compare_roadmaps(previous, revised):
    previous_statuses = {row["code"]: row["status"] for row in previous}
    return [
        {
            "code": row["code"],
            "previous_status": previous_statuses[row["code"]],
            "status": row["status"],
            "requires": row["requires"],
        }
        for row in revised
        if row["code"] in previous_statuses
        and row["status"] != previous_statuses[row["code"]]
    ]
