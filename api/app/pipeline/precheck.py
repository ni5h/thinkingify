"""Automatic pre-checks run before a human ever sees an item.

Recompute every maths answer in code, confirm the answer is actually one of the
options, check the reading level for a nine-year-old, enforce the dedupe
threshold, and run a second-model critique that must find exactly one correct
answer. Any failure is returned (and logged by the caller); a failing item is
never persisted — "failed pre-checks never reach the queue".

Prompts assembled here contain only our own generated item text — never the
private reference set.
"""
from __future__ import annotations

from dataclasses import dataclass

from textstat import textstat

from app.pipeline.adapters.base import TextAdapter
from app.pipeline.maths import recompute
from app.pipeline.types import GeneratedItem

CRITIQUE_SYSTEM = (
    "You are a careful checker for a nine-year-old's quiz. Given a question and "
    "its numbered options, identify every option that is a correct answer. A good "
    "item has exactly one correct option; be strict and flag any that has zero or "
    "more than one."
)

CRITIQUE_TOOL = {
    "name": "critique",
    "description": "Report which options correctly answer the question.",
    "input_schema": {
        "type": "object",
        "required": ["correct_option_indices"],
        "properties": {
            "correct_option_indices": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "0-based indices of every option that is a correct answer.",
            }
        },
    },
}


@dataclass(frozen=True)
class PrecheckFailure:
    check: str
    reason: str


def _critique_prompt(item: GeneratedItem) -> str:
    opts = "\n".join(f"{i}. {o}" for i, o in enumerate(item.options))
    return f"Question: {item.body}\nOptions:\n{opts}"


async def run_prechecks(
    item: GeneratedItem,
    *,
    critique_adapter: TextAdapter,
    reading_grade_max: float,
    dedupe_threshold: float,
) -> list[PrecheckFailure]:
    failures: list[PrecheckFailure] = []

    # 1. Recompute maths answers in code.
    if item.template_id:
        expected = recompute(item)
        if expected != item.answer:
            failures.append(
                PrecheckFailure("maths_recompute", f"answer {item.answer!r} != recomputed {expected!r}")
            )

    # 2. The correct answer must be one of the options.
    if item.answer not in item.options:
        failures.append(PrecheckFailure("answer_in_options", "correct answer is not among the options"))

    # 3. Reading level for a nine-year-old.
    grade = textstat.flesch_kincaid_grade(item.body)
    if grade > reading_grade_max:
        failures.append(PrecheckFailure("reading_level", f"grade {grade:.1f} > {reading_grade_max}"))

    # 4. Dedupe threshold (score set by the dedupe pass).
    if item.dedupe_score is not None and item.dedupe_score >= dedupe_threshold:
        failures.append(
            PrecheckFailure("dedupe", f"similarity {item.dedupe_score:.2f} >= {dedupe_threshold}")
        )

    # 5. Second-model critique: exactly one correct option, and it must be ours.
    try:
        result = await critique_adapter.generate(
            system=CRITIQUE_SYSTEM, prompt=_critique_prompt(item), tool=CRITIQUE_TOOL
        )
        idxs = result.get("correct_option_indices", [])
    except Exception as exc:  # fail closed — an unverifiable item is not queued
        failures.append(PrecheckFailure("critique_error", str(exc)))
    else:
        if not isinstance(idxs, list) or len(idxs) != 1:
            failures.append(
                PrecheckFailure("critique_ambiguous", f"critic found {len(idxs) if isinstance(idxs, list) else '?'} correct options, need exactly 1")
            )
        elif not (0 <= idxs[0] < len(item.options)) or item.options[idxs[0]] != item.answer:
            failures.append(PrecheckFailure("critique_mismatch", "critic's correct option disagrees with our answer"))

    return failures
