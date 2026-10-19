"""Write a generated session to the database as `draft` rows.

Cards and the recap become `asset` rows (ordered, structured `data`); surviving
items become `item` rows linked to their source card. Everything lands as
`draft` so a person must accept it before it goes live — nothing here publishes.
"""
from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.curriculum import Asset, AssetKind, CurriculumStatus, Item, ItemKind
from app.pipeline.types import GeneratedItem, GeneratedSession


async def persist_session(
    db: AsyncSession, session: GeneratedSession, items: list[GeneratedItem]
) -> dict[str, int]:
    concept_id = uuid.UUID(str(session.concept_id))

    card_assets: list[Asset] = []
    for i, card in enumerate(session.cards):
        asset = Asset(
            concept_id=concept_id,
            kind=AssetKind.card,
            order_index=i,
            url=card.visual_url,
            data={
                "title": card.title,
                "text": card.text,
                "visual_brief": card.visual_brief,
                "audio_script": card.audio_script,
                "think": {
                    "q": card.think_q,
                    "options": card.think_options,
                    "answer_index": card.think_answer_index,
                    "why": card.think_why,
                },
            },
            status=CurriculumStatus.draft,
        )
        db.add(asset)
        card_assets.append(asset)

    db.add(
        Asset(
            concept_id=concept_id,
            kind=AssetKind.recap,
            order_index=len(session.cards),
            data={"lines": session.recap.lines, "remember": session.recap.remember},
            status=CurriculumStatus.draft,
        )
    )

    await db.flush()  # assign card asset ids for the source link

    for it in items:
        source_id = None
        if it.source_card_index is not None and 0 <= it.source_card_index < len(card_assets):
            source_id = card_assets[it.source_card_index].id
        db.add(
            Item(
                concept_id=concept_id,
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
    return {"cards": len(session.cards), "items": len(items)}
