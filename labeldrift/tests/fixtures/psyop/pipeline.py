"""Fixture: deliberately contains hardcoded label strings for the scanner to find."""


def classify_priority(score: int) -> str:
    if score > 90:
        return "CRITICAL"  # should be flagged: global rule
    return "LOW"


def classify_risk(value: float) -> str:
    if value > 0.8:
        return "HIGH_RISK"  # should be flagged: context-scoped, path matches "psyop"
    return "CLEAN"
