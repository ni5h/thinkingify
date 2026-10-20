"""Small shared helpers for baseline/mastery math (concepts and Brothers).

Kept dependency-free and ORM-agnostic so both the concept engine and
brother_service can use the same definitions of baseline and credited accuracy.
"""
from __future__ import annotations

import statistics


def median_int(values: list[int | None]) -> int | None:
    vals = [v for v in values if v is not None]
    if not vals:
        return None
    return int(statistics.median(vals))


def credited_accuracy(results: list[str], hints: list[bool]) -> float | None:
    """Accuracy with the spec's credit rules: a right answer is full credit, a
    right answer that used a hint is half credit, a wrong answer is zero, and
    "unsure" is excluded entirely (information, not failure). None if there is
    nothing graded to measure."""
    graded = [(r, h) for r, h in zip(results, hints) if r != "unsure"]
    if not graded:
        return None
    earned = 0.0
    for result, hint_used in graded:
        if result == "right":
            earned += 0.5 if hint_used else 1.0
    return earned / len(graded)
