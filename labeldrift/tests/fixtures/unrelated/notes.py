"""Fixture: 'HIGH_RISK' appears here but this path isn't in the rule's context,
so it must NOT be flagged."""


def describe(level: str) -> str:
    if level == "HIGH_RISK":
        return "elevated"
    return "normal"
