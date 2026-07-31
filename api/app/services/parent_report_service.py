import logging
import uuid
from collections import Counter

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.companion_message import CompanionMessage, CompanionMessageRole
from app.models.content import Content
from app.models.grammar_flag import GrammarFlag, GrammarFlagStatus
from app.models.parent_report import ParentReport
from app.models.sentence_framing_flag import SentenceFramingFlag, SentenceFramingFlagStatus
from app.models.spelling_flag import SpellingFlag, SpellingFlagStatus
from app.models.user import User
from app.schemas.parent_report import ParentReportOut
from app.services import anthropic_client, grammar_concepts, sentence_framing_concepts

_logger = logging.getLogger(__name__)

_MAX_COMPANION_MESSAGES = 30

_SUBMIT_PARENT_REPORT_NARRATIVE_TOOL = {
    "name": "submit_parent_report_narrative",
    "description": "Submit the narrative sections of a parent report about a child's completed writing piece.",
    "input_schema": {
        "type": "object",
        "properties": {
            "headline": {
                "type": "string",
                "description": "One or two plain-language sentences summarizing what the child wrote and how it went.",
            },
            "creativity_narrative": {
                "type": "string",
                "description": (
                    "A few sentences describing the child's creativity and voice in this piece, citing one "
                    "specific phrase or detail actually present in the draft. Never generic praise."
                ),
            },
            "suggested_action": {
                "type": "string",
                "description": (
                    "At most one gentle, optional suggestion for the parent, never phrased as homework. "
                    "Empty string if nothing natural to suggest."
                ),
            },
        },
        "required": ["headline", "creativity_narrative", "suggested_action"],
    },
}

_SYSTEM_PROMPT_TEMPLATE = """\
You are writing a short parent-facing report about {child_name}'s (around \
9 years old) completed piece of writing, for {child_name}'s parent or \
guardian to read.

Hard rules:
- Never compare {child_name} to other kids or to "average for his age" \
— only describe {child_name} relative to {child_name}'s own past work.
- Never lead with what's wrong — describe what happened, not deficits.
- The creativity_narrative must cite ONE specific phrase or detail \
actually present in the draft below — never generic praise like "great \
job" or "nice work." If nothing genuinely specific stands out, describe \
concretely what {child_name} chose to write about instead of inventing \
praise.
- suggested_action is optional — leave it as an empty string unless \
there's a genuinely natural, light-touch idea. It must never feel like \
homework assigned to the parent.
- Keep headline to 1-2 sentences, creativity_narrative to 2-4 sentences, \
suggested_action to 1 sentence or empty.

You must always reply by calling the submit_parent_report_narrative tool.

--- The piece {child_name} wrote (style: {style}) ---
{draft_markdown}

--- Writing buddy chat during this session (for context only, may be empty) ---
{companion_transcript}
"""

_FALLBACK_CREATIVITY = (
    "This piece is ready to read — the specific details of what makes it his own are worth a look together."
)


def _display_name(user: User) -> str:
    return user.username or user.first_name or user.name


def _fallback_headline(author_name: str, title: str) -> str:
    return f'{author_name} finished writing "{title}".'


async def _spelling_breakdown(db: AsyncSession, content_id: uuid.UUID) -> dict:
    result = await db.execute(select(SpellingFlag).where(SpellingFlag.content_id == content_id))
    flags = list(result.scalars().all())
    self_corrected = [f for f in flags if f.status == SpellingFlagStatus.self_corrected]
    # No structured phonics-category field exists on SpellingFlag (hint
    # is free text, not a concept key) — the flagged words themselves are
    # the concrete, real signal to show instead of forcing a category
    # that doesn't structurally exist yet for this stage.
    return {
        "found": len(flags),
        "self_corrected": len(self_corrected),
        "ai_assisted": sum(1 for f in self_corrected if f.hint_revealed),
        "kept_as_is": sum(1 for f in flags if f.status == SpellingFlagStatus.kept_as_is),
        "concepts": sorted({f.word for f in flags}),
    }


async def _grammar_breakdown(db: AsyncSession, content_id: uuid.UUID) -> dict:
    result = await db.execute(select(GrammarFlag).where(GrammarFlag.content_id == content_id))
    flags = list(result.scalars().all())
    return {
        "found": len(flags),
        "self_corrected": sum(1 for f in flags if f.status == GrammarFlagStatus.self_corrected),
        # No reveal/AI-writes-it mechanism exists for Grammar — always 0.
        "ai_assisted": 0,
        "kept_as_is": sum(1 for f in flags if f.status == GrammarFlagStatus.kept_as_is),
        "concepts": sorted({grammar_concepts.CONCEPTS[f.concept_id].label for f in flags}),
        "_concept_counts": Counter(f.concept_id for f in flags),
    }


async def _sentence_framing_breakdown(db: AsyncSession, content_id: uuid.UUID) -> dict:
    result = await db.execute(select(SentenceFramingFlag).where(SentenceFramingFlag.content_id == content_id))
    flags = list(result.scalars().all())
    return {
        "found": len(flags),
        "self_corrected": sum(1 for f in flags if f.status == SentenceFramingFlagStatus.self_corrected),
        "ai_assisted": 0,
        "kept_as_is": sum(1 for f in flags if f.status == SentenceFramingFlagStatus.kept_as_is),
        "concepts": sorted({sentence_framing_concepts.CONCEPTS[f.concept_id].label for f in flags}),
        "_concept_counts": Counter(f.concept_id for f in flags),
    }


async def _companion_stats(db: AsyncSession, content_id: uuid.UUID) -> dict:
    result = await db.execute(
        select(CompanionMessage)
        .where(CompanionMessage.content_id == content_id, CompanionMessage.role == CompanionMessageRole.assistant)
        .order_by(CompanionMessage.created_at)
    )
    messages = list(result.scalars().all())
    return {
        "max_ladder_level": max((m.ladder_level or 1 for m in messages), default=1),
        "direct_answer_requests": sum(1 for m in messages if m.direct_answer_requested),
        "message_count": len(messages),
    }


def _went_well(spelling: dict, grammar: dict, framing: dict, companion: dict) -> list[str]:
    bullets: list[str] = []

    for label, stage in (("spelling", spelling), ("grammar", grammar), ("sentence variety", framing)):
        if stage["found"] > 0 and stage["self_corrected"] == stage["found"] and stage["ai_assisted"] == 0:
            bullets.append(f"Fixed every {label} issue that came up, entirely on his own.")

    if spelling["kept_as_is"] + grammar["kept_as_is"] + framing["kept_as_is"] > 0:
        bullets.append("Made a deliberate choice to keep his own phrasing in a couple of spots.")

    if companion["message_count"] > 0 and companion["direct_answer_requests"] == 0:
        bullets.append("Worked through sticking points in the writing buddy chat without asking for the answer.")

    if not bullets and companion["message_count"] == 0:
        bullets.append("Wrote this one without needing the writing buddy chat at all.")

    return bullets[:3]


def _was_tricky(spelling: dict, grammar: dict, framing: dict, companion: dict) -> list[str]:
    bullets: list[str] = []

    for stage, concept_bank in ((grammar, grammar_concepts.CONCEPTS), (framing, sentence_framing_concepts.CONCEPTS)):
        for concept_id, count in stage["_concept_counts"].items():
            if count >= 2:
                bullets.append(f"{concept_bank[concept_id].label} came up a couple of times.")

    if spelling["ai_assisted"] > 0:
        bullets.append("Needed a hint before fixing a spelling issue.")

    if companion["max_ladder_level"] >= 3:
        bullets.append("Needed a bigger nudge to get unstuck at one point in the writing buddy chat.")

    if companion["direct_answer_requests"] >= 2:
        bullets.append("Asked for the answer directly a couple of times before working it out himself.")

    return bullets[:3]


def _ai_help_level(spelling: dict, grammar: dict, framing: dict, companion: dict) -> str:
    total_ai_assisted = spelling["ai_assisted"] + grammar["ai_assisted"] + framing["ai_assisted"]
    max_ladder = companion["max_ladder_level"]
    direct_requests = companion["direct_answer_requests"]

    if direct_requests >= 3 or total_ai_assisted >= 3:
        return "He needed a bit more support than usual this time — several nudges and a couple of hints along the way."
    if max_ladder >= 3 or direct_requests >= 1 or total_ai_assisted >= 1:
        return "He mostly worked through this on his own, with occasional nudges to get started."
    return "He worked through this mostly independently."


async def generate_report(db: AsyncSession, content: Content) -> ParentReport:
    author_result = await db.execute(select(User).where(User.id == content.author_id))
    author = author_result.scalar_one()
    author_name = _display_name(author)

    spelling = await _spelling_breakdown(db, content.id)
    grammar = await _grammar_breakdown(db, content.id)
    framing = await _sentence_framing_breakdown(db, content.id)
    companion = await _companion_stats(db, content.id)

    went_well = _went_well(spelling, grammar, framing, companion)
    was_tricky = _was_tricky(spelling, grammar, framing, companion)
    ai_help_level = _ai_help_level(spelling, grammar, framing, companion)

    stage_breakdown = {
        "spelling": {k: v for k, v in spelling.items() if not k.startswith("_")},
        "grammar": {k: v for k, v in grammar.items() if not k.startswith("_")},
        "sentence_framing": {k: v for k, v in framing.items() if not k.startswith("_")},
    }

    transcript_result = await db.execute(
        select(CompanionMessage)
        .where(CompanionMessage.content_id == content.id)
        .order_by(CompanionMessage.created_at.desc())
        .limit(_MAX_COMPANION_MESSAGES)
    )
    transcript_messages = list(reversed(transcript_result.scalars().all()))
    companion_transcript = (
        "\n".join(f"{m.role.value}: {m.body}" for m in transcript_messages) or "(no writing buddy chat this session)"
    )

    try:
        system_prompt = _SYSTEM_PROMPT_TEMPLATE.format(
            child_name=author_name,
            style=content.style or "freeform",
            draft_markdown=content.content_markdown.strip() or "(empty draft)",
            companion_transcript=companion_transcript,
        )
        tool_input = await anthropic_client.send_structured(
            system=system_prompt,
            messages=[{"role": "user", "content": "Generate the report now."}],
            tool=_SUBMIT_PARENT_REPORT_NARRATIVE_TOOL,
        )
        headline = str(tool_input.get("headline") or "").strip() or _fallback_headline(author_name, content.title)
        creativity_narrative = str(tool_input.get("creativity_narrative") or "").strip() or _FALLBACK_CREATIVITY
        suggested_action = str(tool_input.get("suggested_action") or "").strip() or None
    except Exception:
        _logger.exception("Parent report narrative generation failed for content_id=%s", content.id)
        headline = _fallback_headline(author_name, content.title)
        creativity_narrative = _FALLBACK_CREATIVITY
        suggested_action = None

    report = ParentReport(
        id=uuid.uuid4(),
        content_id=content.id,
        word_count=len(content.content_markdown.split()),
        headline=headline,
        creativity_narrative=creativity_narrative,
        suggested_action=suggested_action,
        went_well=went_well,
        was_tricky=was_tricky,
        stage_breakdown=stage_breakdown,
        ai_help_level=ai_help_level,
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return report


async def list_for_child(db: AsyncSession, child_id: uuid.UUID) -> list[ParentReportOut]:
    result = await db.execute(
        select(ParentReport, Content)
        .join(Content, Content.id == ParentReport.content_id)
        .where(Content.author_id == child_id)
        .order_by(ParentReport.created_at.desc())
    )
    return [
        ParentReportOut.model_validate(report).model_copy(
            update={"content_title": content.title, "style": content.style}
        )
        for report, content in result.all()
    ]


async def get_by_id(db: AsyncSession, report_id: uuid.UUID) -> tuple[ParentReport, Content] | None:
    result = await db.execute(
        select(ParentReport, Content)
        .join(Content, Content.id == ParentReport.content_id)
        .where(ParentReport.id == report_id)
    )
    row = result.first()
    return (row[0], row[1]) if row else None
