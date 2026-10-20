"""Offline content-pipeline CLI (never served by the API).

    python -m app.pipeline generate --chapter-id <uuid> [--band 2]
    python -m app.pipeline generate --concept-id <uuid>
    python -m app.pipeline dedupe --chapter-id <uuid>
    python -m app.pipeline export-review --chapter-id <uuid> [--out file.json]
    python -m app.pipeline ingest        # local OCR of scans, no model calls

Needs ANTHROPIC_API_KEY for real generation (set pipeline_text_adapter=stub to
dry-run the wiring without a key). Content lands as `draft` for human review.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid

from sqlalchemy import select

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.curriculum import Asset, AssetKind, Chapter, Concept, CurriculumStatus, Item, Subject
from app.pipeline.dedupe import dedupe
from app.pipeline.adapters.registry import get_embedding_adapter
from app.pipeline.reference import load_reference_texts, reference_path
from app.pipeline.run import build_concept
from app.pipeline.types import GeneratedItem


async def _concepts_for(db, *, concept_id: str | None, chapter_id: str | None) -> list[tuple[Concept, str]]:
    """Return (concept, subject_code) for the requested scope."""
    stmt = (
        select(Concept, Subject.code)
        .join(Chapter, Concept.chapter_id == Chapter.id)
        .join(Subject, Chapter.subject_id == Subject.id)
    )
    if concept_id:
        stmt = stmt.where(Concept.id == uuid.UUID(concept_id))
    elif chapter_id:
        stmt = stmt.where(Concept.chapter_id == uuid.UUID(chapter_id)).order_by(Concept.order_index)
    rows = (await db.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def cmd_generate(args) -> None:
    async with AsyncSessionLocal() as db:
        concepts = await _concepts_for(db, concept_id=args.concept_id, chapter_id=args.chapter_id)
        if not concepts:
            sys.exit("No concepts matched.")
        for concept, subject_code in concepts:
            print(f"Concept: {concept.title} ({subject_code})")
            await build_concept(
                db,
                concept_id=str(concept.id),
                title=concept.title,
                subject_code=subject_code,
                band=args.band,
                seed=args.seed,
            )


async def cmd_generate_map(args) -> None:
    from app.pipeline.concept_map import generate_map

    with open(args.file, encoding="utf-8") as fh:
        mapping = json.load(fh)
    only = [t.strip() for t in args.only.split("||")] if args.only else None
    async with AsyncSessionLocal() as db:
        result = await generate_map(db, mapping, only=only)
        print(f"Done. chapter_id={result['chapter_id']} generated {result['generated']}/{result['concepts']} concept(s).")


async def cmd_regen_items(args) -> None:
    from app.pipeline.concept_map import regenerate_map_items

    with open(args.file, encoding="utf-8") as fh:
        mapping = json.load(fh)
    only = [t.strip() for t in args.only.split("||")] if args.only else None
    async with AsyncSessionLocal() as db:
        result = await regenerate_map_items(db, mapping, only=only)
        print(f"Done. regenerated items for {result['regenerated']} concept(s).")


async def cmd_dedupe(args) -> None:
    async with AsyncSessionLocal() as db:
        concepts = await _concepts_for(db, concept_id=args.concept_id, chapter_id=args.chapter_id)
        adapter = get_embedding_adapter()
        refs = load_reference_texts()
        for concept, _ in concepts:
            items = (
                await db.execute(
                    select(Item).where(
                        Item.concept_id == concept.id, Item.status == CurriculumStatus.draft
                    )
                )
            ).scalars().all()
            wrapped = [GeneratedItem(kind=i.kind.value, body=i.body, options=i.options or [], answer=i.answer_key or "", hint=i.hint or "", difficulty=i.difficulty) for i in items]
            _, dropped = dedupe(wrapped, reference_texts=refs, adapter=adapter, threshold=settings.pipeline_dedupe_threshold)
            for src, w in zip(items, wrapped):
                src.dedupe_score = w.dedupe_score
            await db.commit()
            print(f"{concept.title}: scored {len(items)} draft items, {len(dropped)} at/over threshold")


async def cmd_export_review(args) -> None:
    async with AsyncSessionLocal() as db:
        concepts = await _concepts_for(db, concept_id=args.concept_id, chapter_id=args.chapter_id)
        out = []
        for concept, subject_code in concepts:
            assets = (
                await db.execute(
                    select(Asset).where(Asset.concept_id == concept.id, Asset.status == CurriculumStatus.draft).order_by(Asset.order_index)
                )
            ).scalars().all()
            items = (
                await db.execute(
                    select(Item).where(Item.concept_id == concept.id, Item.status == CurriculumStatus.draft)
                )
            ).scalars().all()
            out.append({
                "concept": concept.title,
                "subject": subject_code,
                "cards": [a.data for a in assets if a.kind == AssetKind.card],
                "recap": next((a.data for a in assets if a.kind == AssetKind.recap), None),
                "items": [{"body": i.body, "options": i.options, "answer": i.answer_key, "hint": i.hint, "difficulty": i.difficulty, "dedupe_score": i.dedupe_score} for i in items],
            })
        text = json.dumps(out, indent=2, ensure_ascii=False)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(text)
            print(f"Wrote {args.out}")
        else:
            print(text)


def cmd_ingest(_args) -> None:
    """Local OCR of scans into the gitignored reference folder. No model calls —
    the reference text never leaves the machine or enters a prompt."""
    root = reference_path()
    if not root.exists():
        sys.exit(f"Reference folder {root} does not exist. Create it and add scans locally (it is gitignored).")
    images = [p for p in root.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}]
    if not images:
        print(f"No images to OCR under {root}.")
        return
    try:
        import pytesseract
        from PIL import Image
    except ImportError:
        sys.exit("OCR needs pytesseract + the tesseract binary. Install them locally, then re-run.")
    done = 0
    for img in images:
        target = img.with_suffix(".txt")
        if target.exists():
            continue
        target.write_text(pytesseract.image_to_string(Image.open(img)), encoding="utf-8")
        done += 1
    print(f"OCR'd {done} new image(s) to local .txt (never committed or prompted).")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    g = sub.add_parser("generate", help="generate a card session for a concept/chapter")
    g.add_argument("--concept-id")
    g.add_argument("--chapter-id")
    g.add_argument("--band", type=int, default=2)
    g.add_argument("--seed", type=int, default=None)

    m = sub.add_parser("generate-map", help="seed concepts from a concept-map JSON and generate them")
    m.add_argument("--file", required=True, help="path to the concept-map JSON")
    m.add_argument("--only", help="generate only these concept titles (separate multiple with ||)")

    r = sub.add_parser("regen-items", help="regenerate only the items for existing concepts (keeps cards)")
    r.add_argument("--file", required=True, help="path to the concept-map JSON")
    r.add_argument("--only", help="regenerate only these concept titles (separate multiple with ||)")

    d = sub.add_parser("dedupe", help="re-score draft items against the reference set")
    d.add_argument("--concept-id")
    d.add_argument("--chapter-id")

    e = sub.add_parser("export-review", help="dump draft cards/items as JSON")
    e.add_argument("--concept-id")
    e.add_argument("--chapter-id")
    e.add_argument("--out")

    sub.add_parser("ingest", help="local OCR of private reference scans (no model calls)")

    args = parser.parse_args()
    if args.command == "generate":
        asyncio.run(cmd_generate(args))
    elif args.command == "generate-map":
        asyncio.run(cmd_generate_map(args))
    elif args.command == "regen-items":
        asyncio.run(cmd_regen_items(args))
    elif args.command == "dedupe":
        asyncio.run(cmd_dedupe(args))
    elif args.command == "export-review":
        asyncio.run(cmd_export_review(args))
    elif args.command == "ingest":
        cmd_ingest(args)


if __name__ == "__main__":
    main()
