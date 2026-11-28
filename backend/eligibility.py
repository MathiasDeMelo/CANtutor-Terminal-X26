"""Check completed courses against verified prerequisite rules."""


def meets_prerequisites(required, completed):
    return all(code in completed for code in required)
