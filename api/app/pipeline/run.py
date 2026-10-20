"""Orchestration: generate → dedupe → pre-check → persist, for one concept.

Dropped (deduped) and rejected (failed pre-check) items are reported to the log
and never persisted; only survivors are written as `draft`.
"""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.pipeline.adapters.registry import (
    get_critique_adapter,
    get_embedding_adapter,
    get_generation_adapter,
    get_image_adapter,
)
from app.pipeline.dedupe import dedupe
from app.pipeline.generate import generate_session
from app.pipeline.persist import persist_session
from app.pipeline.precheck import run_prechecks
from app.pipeline.reference import load_reference_texts


async def build_concept(
    db: AsyncSession,
    *,
    concept_id: str,
    title: str,
    subject_code: str,
    band: int = 2,
    description: str = "",
    seed: int | None = None,
    question_styles: list[str] | None = None,
    log: Callable[[str], None] = print,
) -> dict:
    session = await generate_session(
        concept_id=concept_id,
        title=title,
        subject_code=subject_code,
        text_adapter=get_generation_adapter(),
        image_adapter=get_image_adapter(),
        band=band,
        description=description,
        seed=seed,
        question_styles=question_styles,
    )

    kept, dropped = dedupe(
        session.items,
        reference_texts=load_reference_texts(),
        adapter=get_embedding_adapter(),
        threshold=settings.pipeline_dedupe_threshold,
    )
    for it in dropped:
        log(f"  dropped (dedupe {it.dedupe_score:.2f}): {it.body!r}")

    critique = get_critique_adapter()
    survivors = []
    for it in kept:
        failures = await run_prechecks(
            it,
            critique_adapter=critique,
            reading_grade_max=settings.pipeline_reading_grade_max,
            dedupe_threshold=settings.pipeline_dedupe_threshold,
        )
        if failures:
            reasons = "; ".join(f"{f.check}:{f.reason}" for f in failures)
            log(f"  rejected: {it.body!r} :: {reasons}")
        else:
            survivors.append(it)

    counts = await persist_session(db, session, survivors)
    log(
        f"  persisted {counts['cards']} cards + recap, {counts['items']} items "
        f"(dropped {len(dropped)}, rejected {len(kept) - len(survivors)})"
    )
    return {
        "concept_id": concept_id,
        "cards": counts["cards"],
        "items_persisted": counts["items"],
        "dropped": len(dropped),
        "rejected": len(kept) - len(survivors),
    }
