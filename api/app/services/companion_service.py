import logging
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.companion_message import CompanionMessage, CompanionMessageRole
from app.models.content import Content
from app.models.user import User
from app.services import anthropic_client, note_service, topic_service
from app.services.fact_leak_guard import is_fact_leak

_logger = logging.getLogger(__name__)

# Cheap defense against a runaway client bug or button-mashing on a real
# paid API — once hit, the kid gets a graceful in-character wind-down
# instead of the endpoint continuing to call Anthropic.
_MAX_MESSAGES_PER_SESSION = 40

_STYLE_LABELS: dict[str, str] = {
    "fairy_tale": "Fairy Tale",
    "news_report": "News Report",
    "diary_entry": "Diary Entry",
    "letter": "Letter",
    "how_to": "How-To / Instructions",
    "blank": "Freeform",
}

_SESSION_CAP_REPLY = (
    "We've been chatting for a good while — let's give your brain a little rest. "
    "Come back to this later and we'll keep going. What's one thing you want to remember for next time?"
)

_API_FAILURE_REPLY = (
    "Hmm, my brain went a little fuzzy for a second there. Want to try asking that again?"
)

_SYSTEM_PROMPT_TEMPLATE = """\
You are a curious, encouraging writing companion for a child (around 9 \
years old) using a kids' educational app called Thinkingify. Think of \
yourself as a warm older sibling or a curious friend sitting next to \
them while they write — not a teacher, not a quiz bot, and never a \
ghostwriter.

This app has a strict rule everywhere else: the AI never writes content \
for the kid. You are a new, bounded exception that only ever *talks* — \
you help them think, you never draft prose they could paste into their \
own writing.

Hard rules, no exceptions:
- Never state a fact from the topic material below, even to confirm or \
deny something the kid says. If they get a fact wrong, don't correct it \
— ask them a question that helps them notice it themselves, or don't \
engage with the fact at all.
- Never write a sentence or phrase the kid could paste directly into \
their draft. Always speak to them in second person, coaching register \
("What if the story started with...?") — never in narrative/descriptive \
register ("The owl flew...").
- Every single reply must end in a question or a small, concrete, \
actionable nudge.
- If the kid directly asks you for the answer or asks you to just write \
it for them: acknowledge how they're feeling, don't scold them, and \
redirect gently.

Response ladder — use the lowest level that fits, and only escalate if \
the kid is still stuck on the exact same thing across multiple turns \
(reset back toward level 1 the moment they ask about something new):
1. Open question — "What part of this did you find interesting?"
2. Point to their own material — "You wrote X in your notes — what made \
you think that?"
3. Reduce scope — "Forget the whole story for a second — just tell me \
one sentence about the beginning."
4. Process nudge, never content — "Want to just write something messy \
and we'll fix it up after?"

Praise policy: no unprompted evaluative praise ("great job!", "amazing!"). \
A light acknowledgment of effort or movement is fine ("Nice, you \
started!"), but nothing more — save real praise for later.

Off-topic handling: if the kid goes off on a tangent, follow it briefly \
and warmly, redirect gently once, and don't act like a rigid enforcer.

You must always reply by calling the submit_reply tool. `reply` is the \
warm, short message the kid will actually see. `ladder_level` is your \
honest assessment of which level above best matches this reply. \
`direct_answer_requested` is true only if the kid's latest message was \
asking you to just give them the answer or the content directly.
{session_state}

--- Topic material (for your own context only — never repeat or quote \
this to the kid) ---
{topic_context}

--- The kid's own notes on this topic ---
{notes_context}

--- The kid's current draft ({style_label} style) ---
{draft_context}
"""


def _build_system_prompt(
    *,
    topic_explainer: str,
    audio_transcript: str | None,
    notes_body: str,
    draft_markdown: str,
    style: str | None,
    current_ladder_level: int,
    consecutive_direct_answer_count: int,
) -> str:
    topic_context = topic_explainer.strip()
    if audio_transcript and audio_transcript.strip():
        topic_context += "\n\n" + audio_transcript.strip()

    session_state = f"\nCurrent ladder level so far this session: {current_ladder_level}."
    if consecutive_direct_answer_count >= 2:
        session_state += (
            " The kid has now asked you for the direct answer more than once in a row. "
            "Gently and kindly name this pattern out loud before redirecting again — "
            "don't pretend not to notice."
        )

    return _SYSTEM_PROMPT_TEMPLATE.format(
        session_state=session_state,
        topic_context=topic_context or "(no topic material available)",
        notes_context=notes_body.strip() or "(no notes yet)",
        draft_context=draft_markdown.strip() or "(nothing written yet)",
        style_label=_STYLE_LABELS.get(style or "", "Freeform"),
    )


def _ends_in_nudge(reply: str) -> bool:
    return reply.strip().endswith("?")


def _repair_missing_nudge(reply: str) -> str:
    if _ends_in_nudge(reply):
        return reply
    return f"{reply.rstrip()} What do you think you'll try next?"


async def _session_state(
    db: AsyncSession, content_id: uuid.UUID, user_id: uuid.UUID, session_id: uuid.UUID
) -> tuple[list[CompanionMessage], int, int]:
    result = await db.execute(
        select(CompanionMessage)
        .where(
            CompanionMessage.content_id == content_id,
            CompanionMessage.user_id == user_id,
            CompanionMessage.session_id == session_id,
        )
        .order_by(CompanionMessage.created_at)
    )
    session_messages = list(result.scalars().all())

    assistant_messages = [m for m in session_messages if m.role == CompanionMessageRole.assistant]
    current_ladder_level = assistant_messages[-1].ladder_level if assistant_messages else 1

    consecutive_direct_answer_count = 0
    for message in reversed(assistant_messages):
        if message.direct_answer_requested:
            consecutive_direct_answer_count += 1
        else:
            break

    return session_messages, (current_ladder_level or 1), consecutive_direct_answer_count


def _to_anthropic_messages(session_messages: list[CompanionMessage]) -> list[dict[str, str]]:
    return [
        {"role": m.role.value, "content": m.body}
        for m in session_messages
    ]


async def list_messages(db: AsyncSession, content: Content) -> list[CompanionMessage]:
    result = await db.execute(
        select(CompanionMessage)
        .where(CompanionMessage.content_id == content.id)
        .order_by(CompanionMessage.created_at)
    )
    return list(result.scalars().all())


async def send_message(
    db: AsyncSession,
    current_user: User,
    content: Content,
    session_id: uuid.UUID,
    user_text: str,
) -> CompanionMessage:
    if content.topic_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="This draft isn't linked to a topic yet."
        )

    topic = await topic_service.get_by_id(db, content.topic_id)
    if topic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found.")
    note = await note_service.get_or_create(db, current_user, content.topic_id)

    # Persist the kid's own words before ever calling the LLM — never lose
    # them to an API failure.
    user_message = CompanionMessage(
        id=uuid.uuid4(),
        content_id=content.id,
        user_id=current_user.id,
        session_id=session_id,
        role=CompanionMessageRole.user,
        body=user_text,
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    session_messages, current_ladder_level, consecutive_direct_answer_count = await _session_state(
        db, content.id, current_user.id, session_id
    )

    if len(session_messages) > _MAX_MESSAGES_PER_SESSION:
        return await _persist_assistant_reply(
            db,
            content=content,
            user_id=current_user.id,
            session_id=session_id,
            reply=_SESSION_CAP_REPLY,
            ladder_level=current_ladder_level,
            direct_answer_requested=False,
            fact_leak_blocked=False,
            is_fallback=True,
        )

    # Everything from prompt assembly through the backstop/repair steps is
    # wrapped in one broad handler: the kid must never see a raw error from
    # any of it — an Anthropic HTTP failure, a malformed tool response, or
    # a bug in the leak/repair logic all fail the same way, soft toward
    # the kid (an in-character reply) and loud toward the logs.
    try:
        system_prompt = _build_system_prompt(
            topic_explainer=topic.explainer_markdown,
            audio_transcript=topic.audio_transcript,
            notes_body=note.body,
            draft_markdown=content.content_markdown,
            style=content.style,
            current_ladder_level=current_ladder_level,
            consecutive_direct_answer_count=consecutive_direct_answer_count,
        )
        tool_input = await anthropic_client.send_structured(
            system=system_prompt, messages=_to_anthropic_messages(session_messages)
        )
        reply = str(tool_input["reply"])
        ladder_level = int(tool_input.get("ladder_level", current_ladder_level))
        direct_answer_requested = bool(tool_input.get("direct_answer_requested", False))

        # Model can de-escalate freely; can't jump more than one rung per turn.
        ladder_level = max(1, min(ladder_level, current_ladder_level + 1, 4))

        fact_leak_blocked = is_fact_leak(reply, topic.explainer_markdown, topic.audio_transcript)
        if fact_leak_blocked:
            reply = "Hmm, let's think about this together — what part of the topic stood out to you the most?"
        else:
            reply = _repair_missing_nudge(reply)
    except Exception:
        _logger.exception(
            "Companion reply failed for content_id=%s session_id=%s", content.id, session_id
        )
        return await _persist_assistant_reply(
            db,
            content=content,
            user_id=current_user.id,
            session_id=session_id,
            reply=_API_FAILURE_REPLY,
            ladder_level=current_ladder_level,
            direct_answer_requested=False,
            fact_leak_blocked=False,
            is_fallback=True,
        )

    return await _persist_assistant_reply(
        db,
        content=content,
        user_id=current_user.id,
        session_id=session_id,
        reply=reply,
        ladder_level=ladder_level,
        direct_answer_requested=direct_answer_requested,
        fact_leak_blocked=fact_leak_blocked,
        is_fallback=False,
    )


async def _persist_assistant_reply(
    db: AsyncSession,
    *,
    content: Content,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    reply: str,
    ladder_level: int,
    direct_answer_requested: bool,
    fact_leak_blocked: bool,
    is_fallback: bool,
) -> CompanionMessage:
    assistant_message = CompanionMessage(
        id=uuid.uuid4(),
        content_id=content.id,
        user_id=user_id,
        session_id=session_id,
        role=CompanionMessageRole.assistant,
        body=reply,
        ladder_level=ladder_level,
        direct_answer_requested=direct_answer_requested,
        fact_leak_blocked=fact_leak_blocked,
        is_fallback=is_fallback,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    return assistant_message
