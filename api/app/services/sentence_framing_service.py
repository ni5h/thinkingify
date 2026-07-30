import re
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.sentence_framing_flag import SentenceFramingFlag, SentenceFramingFlagStatus
from app.schemas.sentence_framing import ExamplePairOut, SentenceFramingFlagOut
from app.services import sentence_framing_concepts

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[A-Za-z']+")

_MIN_RUN = 3
_CHOPPY_MAX_WORDS = 5


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]


def _first_word(sentence: str) -> str | None:
    match = _WORD_RE.match(sentence.strip())
    return match.group(0).lower() if match else None


def _word_count(sentence: str) -> int:
    return len(_WORD_RE.findall(sentence))


def _detect_repeated_openings(sentences: list[str]) -> list[list[str]]:
    """3+ consecutive sentences sharing the same first word."""
    groups: list[list[str]] = []
    run: list[str] = []
    run_word: str | None = None
    for sentence in sentences:
        word = _first_word(sentence)
        if word is not None and word == run_word:
            run.append(sentence)
        else:
            if len(run) >= _MIN_RUN:
                groups.append(run)
            run = [sentence]
            run_word = word
    if len(run) >= _MIN_RUN:
        groups.append(run)
    return groups


def _detect_choppy_runs(sentences: list[str]) -> list[list[str]]:
    """3+ consecutive sentences all at or under _CHOPPY_MAX_WORDS words."""
    groups: list[list[str]] = []
    run: list[str] = []
    for sentence in sentences:
        if 0 < _word_count(sentence) <= _CHOPPY_MAX_WORDS:
            run.append(sentence)
        else:
            if len(run) >= _MIN_RUN:
                groups.append(run)
            run = []
    if len(run) >= _MIN_RUN:
        groups.append(run)
    return groups


_DETECTORS: dict[str, Callable[[list[str]], list[list[str]]]] = {
    "repeated_sentence_openings": _detect_repeated_openings,
    "choppy_short_sentences": _detect_choppy_runs,
}


async def _existing_flags_by_key(
    db: AsyncSession, content_id: uuid.UUID
) -> dict[tuple[str, str], SentenceFramingFlag]:
    result = await db.execute(select(SentenceFramingFlag).where(SentenceFramingFlag.content_id == content_id))
    return {(flag.concept_id, flag.sentences): flag for flag in result.scalars().all()}


def _upsert(
    db: AsyncSession,
    existing_by_key: dict[tuple[str, str], SentenceFramingFlag],
    *,
    content_id: uuid.UUID,
    concept_id: str,
    sentences: str,
) -> None:
    key = (concept_id, sentences)
    existing = existing_by_key.get(key)
    if existing is None:
        flag = SentenceFramingFlag(
            id=uuid.uuid4(),
            content_id=content_id,
            concept_id=concept_id,
            sentences=sentences,
            status=SentenceFramingFlagStatus.pending,
        )
        db.add(flag)
        existing_by_key[key] = flag
        return

    if existing.status == SentenceFramingFlagStatus.kept_as_is:
        return
    if existing.status == SentenceFramingFlagStatus.self_corrected:
        # Same run, same concept, detected again — the kid re-typed (or
        # reverted) the exact same pattern, a fresh instance of the issue.
        existing.status = SentenceFramingFlagStatus.pending
        existing.attempt_count = 0
        existing.resolved_at = None


async def run_check(db: AsyncSession, content: Content, sections: list[str]) -> list[SentenceFramingFlag]:
    """Detects runs *within* each section independently — never across a
    section boundary. Spelling's word-level and Grammar's sentence-level
    flags can't span a section join, but a run of 3+ consecutive
    sentences legitimately could if detection ran against the flattened
    whole-draft text — that would produce a flag whose text doesn't exist
    as a literal substring in any single section's markdown, silently
    breaking correction-application. Keeping detection per-section avoids
    this entirely."""
    active_concepts = sentence_framing_concepts.active_concepts_for_style(content.style)
    if not active_concepts:
        return await list_pending(db, content)

    existing_by_key = await _existing_flags_by_key(db, content.id)

    for section_text in sections:
        sentences = _split_sentences(section_text)
        for concept in active_concepts:
            for group in _DETECTORS[concept.id](sentences):
                _upsert(
                    db,
                    existing_by_key,
                    content_id=content.id,
                    concept_id=concept.id,
                    sentences=" ".join(group),
                )

    await db.commit()
    return await list_pending(db, content)


async def attempt_fix(db: AsyncSession, flag: SentenceFramingFlag, rewritten_text: str) -> SentenceFramingFlag:
    sentences = _split_sentences(rewritten_text.strip())
    still_present = len(_DETECTORS[flag.concept_id](sentences)) > 0

    if not still_present:
        flag.status = SentenceFramingFlagStatus.self_corrected
        flag.resolved_at = datetime.now(UTC)
    else:
        flag.attempt_count += 1

    await db.commit()
    await db.refresh(flag)
    return flag


async def override(db: AsyncSession, flag: SentenceFramingFlag) -> SentenceFramingFlag:
    if flag.attempt_count < 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Try a couple of rewrites first.",
        )
    flag.status = SentenceFramingFlagStatus.kept_as_is
    flag.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(flag)
    return flag


async def get_flag(db: AsyncSession, flag_id: uuid.UUID) -> SentenceFramingFlag | None:
    result = await db.execute(select(SentenceFramingFlag).where(SentenceFramingFlag.id == flag_id))
    return result.scalar_one_or_none()


async def list_pending(db: AsyncSession, content: Content) -> list[SentenceFramingFlag]:
    result = await db.execute(
        select(SentenceFramingFlag)
        .where(SentenceFramingFlag.content_id == content.id, SentenceFramingFlag.status == SentenceFramingFlagStatus.pending)
        .order_by(SentenceFramingFlag.created_at)
    )
    return list(result.scalars().all())


def to_out(flag: SentenceFramingFlag) -> SentenceFramingFlagOut:
    concept = sentence_framing_concepts.CONCEPTS[flag.concept_id]
    return SentenceFramingFlagOut.model_validate(flag).model_copy(
        update={
            "concept_label": concept.label,
            "concept_rule": concept.rule,
            "example_pairs": [ExamplePairOut(incorrect=e.incorrect, correct=e.correct) for e in concept.examples],
        }
    )
