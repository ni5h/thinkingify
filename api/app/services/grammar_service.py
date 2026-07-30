import logging
import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content import Content
from app.models.grammar_flag import GrammarFlag, GrammarFlagStatus
from app.schemas.grammar import ExamplePairOut, GrammarFlagOut
from app.services import anthropic_client, grammar_concepts
from app.services.anthropic_client import AnthropicClientError
from app.services.grammar_concepts import GrammarConcept

_logger = logging.getLogger(__name__)

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_MAX_SENTENCES_PER_CHECK = 30

_SUBMIT_GRAMMAR_JUDGMENTS_TOOL = {
    "name": "submit_grammar_judgments",
    "description": "Submit your grammar judgment for each numbered sentence.",
    "input_schema": {
        "type": "object",
        "properties": {
            "judgments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "The item number this judgment is for."},
                        "violates": {
                            "type": "boolean",
                            "description": "True only if the sentence clearly violates one of the given concepts.",
                        },
                        "concept_id": {
                            "type": "string",
                            "description": "Which concept id is violated (must be one of the given ids), or an empty string if none.",
                        },
                    },
                    "required": ["index", "violates", "concept_id"],
                },
            }
        },
        "required": ["judgments"],
    },
}

_SYSTEM_PROMPT_TEMPLATE = """\
You are checking a child's (around 9 years old) writing for a small, \
specific set of grammar issues — nothing else. Only flag a sentence if \
it clearly violates one of the concepts below; when in doubt, don't \
flag it. Never invent a concept id that isn't listed here.

Concepts:
{concepts_block}

For each numbered sentence, decide whether it violates ANY of the \
concepts above. Always call submit_grammar_judgments with one judgment \
per numbered item, in the same order. If a sentence is fine, set \
violates to false and concept_id to "".
"""


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]


def _concepts_block(concepts: list[GrammarConcept]) -> str:
    lines = []
    for concept in concepts:
        examples = "; ".join(f'"{e.incorrect}" -> "{e.correct}"' for e in concept.examples)
        lines.append(f"- {concept.id}: {concept.rule} Examples: {examples}")
    return "\n".join(lines)


async def _judge_sentences(sentences: list[str], concepts: list[GrammarConcept]) -> list[dict | None]:
    """Batched (or single-item, for attempt_fix's scoped re-check) sentence
    judgment against the given concept set. Returns one entry per input
    sentence — None everywhere if the call fails entirely (fail-soft:
    caller decides what "no answer" means for its situation)."""
    system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(concepts_block=_concepts_block(concepts))
    numbered = "\n".join(f'{i + 1}. "{sentence}"' for i, sentence in enumerate(sentences))

    try:
        tool_input = await anthropic_client.send_structured(
            system=system_prompt,
            messages=[{"role": "user", "content": numbered}],
            tool=_SUBMIT_GRAMMAR_JUDGMENTS_TOOL,
        )
    except AnthropicClientError:
        _logger.exception("Grammar check failed")
        return [None] * len(sentences)

    judgments = tool_input.get("judgments")
    if not isinstance(judgments, list):
        return [None] * len(sentences)

    by_index: dict[int, dict] = {}
    for entry in judgments:
        if isinstance(entry, dict) and isinstance(entry.get("index"), int):
            by_index[entry["index"]] = entry
    return [by_index.get(i + 1) for i in range(len(sentences))]


async def _existing_flags_by_key(db: AsyncSession, content_id: uuid.UUID) -> dict[tuple[str, str], GrammarFlag]:
    result = await db.execute(select(GrammarFlag).where(GrammarFlag.content_id == content_id))
    return {(flag.concept_id, flag.sentence): flag for flag in result.scalars().all()}


def _upsert(
    db: AsyncSession,
    existing_by_key: dict[tuple[str, str], GrammarFlag],
    *,
    content_id: uuid.UUID,
    concept_id: str,
    sentence: str,
) -> None:
    key = (concept_id, sentence)
    existing = existing_by_key.get(key)
    if existing is None:
        flag = GrammarFlag(
            id=uuid.uuid4(),
            content_id=content_id,
            concept_id=concept_id,
            sentence=sentence,
            status=GrammarFlagStatus.pending,
        )
        db.add(flag)
        existing_by_key[key] = flag
        return

    if existing.status == GrammarFlagStatus.kept_as_is:
        return
    if existing.status == GrammarFlagStatus.self_corrected:
        # Same sentence, same concept, flagged again — the kid re-typed
        # the exact same mistake elsewhere (or reverted an edit). A fresh
        # instance of the same issue, so reopen it.
        existing.status = GrammarFlagStatus.pending
        existing.attempt_count = 0
        existing.resolved_at = None


async def run_check(db: AsyncSession, content: Content, text: str) -> list[GrammarFlag]:
    active_concepts = grammar_concepts.active_concepts_for_style(content.style)
    sentences = _split_sentences(text)[:_MAX_SENTENCES_PER_CHECK]
    if not sentences or not active_concepts:
        return await list_pending(db, content)

    judgments = await _judge_sentences(sentences, active_concepts)
    active_concept_ids = {c.id for c in active_concepts}
    existing_by_key = await _existing_flags_by_key(db, content.id)

    for sentence, judgment in zip(sentences, judgments):
        if judgment is None or not judgment.get("violates"):
            continue
        concept_id = judgment.get("concept_id")
        if concept_id not in active_concept_ids:
            continue
        _upsert(db, existing_by_key, content_id=content.id, concept_id=concept_id, sentence=sentence)

    await db.commit()
    return await list_pending(db, content)


async def attempt_fix(db: AsyncSession, flag: GrammarFlag, rewritten_sentence: str) -> GrammarFlag:
    rewritten_sentence = rewritten_sentence.strip()
    concept = grammar_concepts.CONCEPTS[flag.concept_id]

    judgments = await _judge_sentences([rewritten_sentence], [concept])
    judgment = judgments[0]
    if judgment is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not check that just now — try again in a moment.",
        )

    if not judgment.get("violates"):
        flag.status = GrammarFlagStatus.self_corrected
        flag.resolved_at = datetime.now(UTC)
    else:
        flag.attempt_count += 1

    await db.commit()
    await db.refresh(flag)
    return flag


async def override(db: AsyncSession, flag: GrammarFlag) -> GrammarFlag:
    if flag.attempt_count < 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Try a couple of rewrites first.",
        )
    flag.status = GrammarFlagStatus.kept_as_is
    flag.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(flag)
    return flag


async def get_flag(db: AsyncSession, flag_id: uuid.UUID) -> GrammarFlag | None:
    result = await db.execute(select(GrammarFlag).where(GrammarFlag.id == flag_id))
    return result.scalar_one_or_none()


async def list_pending(db: AsyncSession, content: Content) -> list[GrammarFlag]:
    result = await db.execute(
        select(GrammarFlag)
        .where(GrammarFlag.content_id == content.id, GrammarFlag.status == GrammarFlagStatus.pending)
        .order_by(GrammarFlag.created_at)
    )
    return list(result.scalars().all())


def to_out(flag: GrammarFlag) -> GrammarFlagOut:
    """Joins a flag with its concept bank entry for the API response —
    concept_label/rule/examples are a pure function of concept_id, so
    they're resolved here rather than duplicated on the row (see
    content_service.py's ContentOut author-join for the same "denormalize
    joined data into the output schema" precedent)."""
    concept = grammar_concepts.CONCEPTS[flag.concept_id]
    return GrammarFlagOut.model_validate(flag).model_copy(
        update={
            "concept_label": concept.label,
            "concept_rule": concept.rule,
            "example_pairs": [ExamplePairOut(incorrect=e.incorrect, correct=e.correct) for e in concept.examples],
        }
    )
