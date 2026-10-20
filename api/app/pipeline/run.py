"""Orchestration: generate → dedupe → pre-check → persist, for one concept.

Dropped (deduped) and rejected (failed pre-check) items are reported to the log
and never persisted; only survivors are written as `draft`.
"""
from __future__ import annotations

import uuid
from collections.abc import Callable

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.curriculum import Asset, AssetKind, CurriculumStatus, Item, ItemKind
from app.pipeline import maths
from app.pipeline.adapters.registry import (
    get_critique_adapter,
    get_embedding_adapter,
    get_generation_adapter,
    get_image_adapter,
)
from app.pipeline.dedupe import dedupe
from app.pipeline.generate import (
    ITEMS_SYSTEM,
    ITEMS_TOOL,
    _item_from,
    build_items_prompt,
    generate_session,
)
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


async def regenerate_items(
    db: AsyncSession,
    *,
    concept_id: str,
    title: str,
    subject_code: str,
    band: int = 2,
    question_styles: list[str] | None = None,
    log: Callable[[str], None] = print,
) -> dict:
    """Regenerate only the quick-check items for a concept, keeping its existing
    cards. Replaces that concept's draft items with the survivors."""
    cid = uuid.UUID(str(concept_id))
    card_assets = (
        await db.execute(
            select(Asset)
            .where(Asset.concept_id == cid, Asset.kind == AssetKind.card)
            .order_by(Asset.order_index)
        )
    ).scalars().all()
    card_titles = [(a.data or {}).get("title", "") for a in card_assets]

    if subject_code == "maths":
        items = maths.generate_items(band=band, n=5)
    else:
        gen = get_generation_adapter()
        idata = await gen.generate(
            system=ITEMS_SYSTEM,
            prompt=build_items_prompt(
                title=title, card_titles=card_titles, band=band, question_styles=question_styles or []
            ),
            tool=ITEMS_TOOL,
        )
        items = [_item_from(d, len(card_assets)) for d in idata.get("items", [])]

    kept, dropped = dedupe(
        items,
        reference_texts=load_reference_texts(),
        adapter=get_embedding_adapter(),
        threshold=settings.pipeline_dedupe_threshold,
    )
    critique = get_critique_adapter()
    survivors = []
    for it in kept:
        failures = await run_prechecks(
            it,
            critique_adapter=critique,
            reading_grade_max=settings.pipeline_reading_grade_max,
            dedupe_threshold=settings.pipeline_dedupe_threshold,
        )
        if not failures:
            survivors.append(it)

    await db.execute(delete(Item).where(Item.concept_id == cid, Item.status == CurriculumStatus.draft))
    for it in survivors:
        source_id = None
        if it.source_card_index is not None and 0 <= it.source_card_index < len(card_assets):
            source_id = card_assets[it.source_card_index].id
        db.add(
            Item(
                id=uuid.uuid4(),
                concept_id=cid,
                kind=ItemKind(it.kind),
                difficulty=it.difficulty,
                body=it.body,
                options=it.options,
                answer_key=it.answer,
                hint=it.hint,
                source_asset_id=source_id,
                dedupe_score=it.dedupe_score,
                status=CurriculumStatus.draft,
            )
        )
    await db.commit()
    log(f"  {title}: {len(survivors)} items (dropped {len(dropped)}, rejected {len(kept) - len(survivors)})")
    return {"title": title, "items": len(survivors)}
