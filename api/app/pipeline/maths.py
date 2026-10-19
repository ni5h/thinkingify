"""Maths items with numbers and answers computed in code.

Per the content rule, a model never decides a maths answer: these templates
generate the numbers, the correct answer and the distractors deterministically
(seeded), and `recompute` re-derives the answer from the stored params so a
pre-check can verify it. The model's only job for maths is wording/context on
the cards, never the arithmetic.
"""
from __future__ import annotations

import random

from app.pipeline.types import GeneratedItem

# Index = power of ten (Ones=10^0 ... Thousands=10^3).
HOUSES = ["Ones", "Tens", "Hundreds", "Thousands"]


def _comma(n: int) -> str:
    return f"{n:,}"


def _digits(rng: random.Random, n_digits: int) -> list[int]:
    return [rng.randint(1, 9)] + [rng.randint(0, 9) for _ in range(n_digits - 1)]


def _to_int(digits: list[int]) -> int:
    return int("".join(str(d) for d in digits))


def _nonzero_positions(digits: list[int]) -> list[int]:
    # positions from the right whose digit is non-zero
    n = len(digits)
    return [n - 1 - i for i, d in enumerate(digits) if d != 0]


# ---- templates: each returns a GeneratedItem carrying template_id + params ----

def _digit_worth(rng: random.Random, band: int) -> GeneratedItem:
    n = 3 if band <= 1 else 4
    digits = _digits(rng, n)
    pos = rng.choice(_nonzero_positions(digits))
    digit = digits[n - 1 - pos]
    number = _to_int(digits)
    worth = digit * (10 ** pos)
    options = sorted({digit * (10 ** p) for p in range(n)} | {worth})
    return GeneratedItem(
        kind="recall",
        body=f"In {_comma(number)}, what is the digit in the {HOUSES[pos]} place worth?",
        options=[_comma(o) for o in options],
        answer=_comma(worth),
        hint=f"The digit in the {HOUSES[pos]} place is worth {HOUSES[pos].lower()}.",
        difficulty=band,
        template_id="digit_worth",
        params={"digits": digits, "pos": pos},
    )


def _expanded_form(rng: random.Random, band: int) -> GeneratedItem:
    n = 3 if band <= 1 else 4
    digits = _digits(rng, n)
    number = _to_int(digits)
    parts = [digits[n - 1 - p] * (10 ** p) for p in range(n - 1, -1, -1) if digits[n - 1 - p] != 0]
    summ = " + ".join(_comma(p) for p in parts)
    # Deterministic distractors by fixed offsets, so the answer is always one of
    # four distinct options (a wrong option need not be a formable number).
    options = sorted({number, number + 90, number + 100, number + 900})
    return GeneratedItem(
        kind="apply",
        body=f"Which number is {summ}?",
        options=[_comma(o) for o in options],
        answer=_comma(number),
        hint="Add the thousands, hundreds, tens and ones, keeping each in its place.",
        difficulty=band,
        template_id="expanded_form",
        params={"digits": digits},
    )


def _compare(rng: random.Random, band: int) -> GeneratedItem:
    n = 3 if band <= 1 else 4
    a = _to_int(_digits(rng, n))
    b = _to_int(_digits(rng, n))
    while b == a:
        b = _to_int(_digits(rng, n))
    bigger = max(a, b)
    return GeneratedItem(
        kind="recall",
        body=f"Which is bigger, {_comma(a)} or {_comma(b)}?",
        options=[_comma(a), _comma(b)],
        answer=_comma(bigger),
        hint="Start at the biggest place and move right; the first place that differs decides.",
        difficulty=band,
        template_id="compare",
        params={"a": a, "b": b},
    )


def _build_biggest(rng: random.Random, band: int) -> GeneratedItem:
    n = 3 if band <= 1 else 4
    digits = [rng.randint(1, 9) for _ in range(n)]
    biggest = int("".join(str(d) for d in sorted(digits, reverse=True)))
    smallest = int("".join(str(d) for d in sorted(digits)))
    middle = _to_int(digits)
    options = sorted({biggest, smallest, middle})
    tiles = ", ".join(str(d) for d in digits)
    return GeneratedItem(
        kind="apply",
        body=f"Using the digits {tiles}, what is the biggest number you can make?",
        options=[_comma(o) for o in options],
        answer=_comma(biggest),
        hint="Put the biggest digit in the most valuable place.",
        difficulty=band,
        template_id="build_biggest",
        params={"digits": digits},
    )


_TEMPLATES = {
    "digit_worth": _digit_worth,
    "expanded_form": _expanded_form,
    "compare": _compare,
    "build_biggest": _build_biggest,
}
_ORDER = ["digit_worth", "expanded_form", "compare", "build_biggest"]


def generate_items(*, band: int = 2, n: int = 5, seed: int | None = None) -> list[GeneratedItem]:
    """n maths check items across the templates, with answers computed in code."""
    rng = random.Random(seed)
    items: list[GeneratedItem] = []
    for i in range(n):
        template = _TEMPLATES[_ORDER[i % len(_ORDER)]]
        items.append(template(rng, band))
    return items


def recompute(item: GeneratedItem) -> str:
    """Re-derive the correct answer from the stored params (pre-check uses this
    to confirm the generated answer wasn't corrupted)."""
    p = item.params
    if item.template_id == "digit_worth":
        digits, pos = p["digits"], p["pos"]
        return _comma(digits[len(digits) - 1 - pos] * (10 ** pos))
    if item.template_id == "expanded_form":
        return _comma(_to_int(p["digits"]))
    if item.template_id == "compare":
        return _comma(max(p["a"], p["b"]))
    if item.template_id == "build_biggest":
        return _comma(int("".join(str(d) for d in sorted(p["digits"], reverse=True))))
    raise ValueError(f"No recompute for template {item.template_id!r}")
