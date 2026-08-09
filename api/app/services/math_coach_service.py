import logging
import re
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.math_coach_message import MathCoachMessage, MathCoachMessageRole
from app.models.math_problem import MathAnswerKind, MathProblem
from app.models.user import User
from app.services import anthropic_client
from app.services.fact_leak_guard import is_fact_leak

_logger = logging.getLogger(__name__)

# Same runaway-cost backstop as the writing companion — once hit, the kid
# gets a graceful wind-down instead of the endpoint continuing to call a
# paid API.
_MAX_MESSAGES_PER_SESSION = 40

_SESSION_CAP_REPLY = (
    "We've been at this one for a good while — let's give your brain a rest. "
    "Come back to it later with fresh eyes. What's the one thing you've figured out so far?"
)

_API_FAILURE_REPLY = "Hmm, my brain went fuzzy for a second there. Want to tell me what you've tried so far?"

_ANSWER_LEAK_REPLY = (
    "I nearly gave too much away there! Let's keep it yours. "
    "What's the very next small step you could try in your head?"
)

_SUBMIT_COACH_REPLY_TOOL = {
    "name": "submit_coach_reply",
    "description": (
        "Submit your reply to the kid, plus your assessment of this turn. "
        "Always call this tool instead of replying directly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "Your warm, short reply — a question or nudge that helps the kid think, never the answer.",
            },
            "ladder_level": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4,
                "description": (
                    "How much of a nudge this reply is: 1=open question about the problem, "
                    "2=point to a strategy (smaller case, spot a pattern, estimate), "
                    "3=reduce the scope to just the first step, 4=process nudge. "
                    "Use 1 unless the kid is stuck on the exact same thing as last turn."
                ),
            },
            "asked_for_answer": {
                "type": "boolean",
                "description": "True if the kid's message was asking you to just tell them the answer.",
            },
        },
        "required": ["reply", "ladder_level", "asked_for_answer"],
    },
}

_SYSTEM_PROMPT_TEMPLATE = """\
You are a warm, curious maths coach sitting next to a child (around 9 \
years old) who is working on an olympiad-style problem. Think of \
yourself like the mathematician Ramanujan's encouraging friend — someone \
who loves spotting patterns and helping the kid discover things for \
themselves. You are NOT a teacher lecturing, and NEVER a solver who does \
it for them.

Hard rules, no exceptions:
- NEVER state the answer, and never reveal or quote the worked solution \
below — not even to confirm or check the kid's guess. If they guess, \
don't say whether it's right; ask them how they could check it \
themselves.
- NEVER do the calculation for them or write out the steps. Nudge their \
thinking; let them do the maths.
- Push for MENTAL strategies. Ask things like "can you do that in your \
head?", "is there a shortcut?", "could you break that into easier \
pieces?" — help them build number sense, not reach for paper.
- Every single reply must end in a question or one small, concrete, \
doable nudge.
- If the kid directly asks for the answer: acknowledge how they feel, \
don't scold, and gently redirect to a thinking step.

Nudge ladder — use the LOWEST level that fits, and only escalate if the \
kid is still stuck on the exact same thing across turns (drop back to 1 \
the moment they try something new):
1. Open question — "What is this problem actually asking? What do you \
already know?"
2. Point to a strategy — "Could you try it with smaller numbers first? \
Do you see a pattern? Could you estimate roughly before solving?"
3. Reduce the scope — "Forget the whole thing for a second — what's the \
very first small step you could figure out?"
4. Process nudge, never content — "Want to just try something and see \
what happens? What would you guess, and how could you check it?"

Praise policy: no empty praise ("amazing!", "genius!"). A light nod to \
effort is fine ("Nice, you spotted something") — save real praise for \
when they crack it themselves.

You must always reply by calling the submit_coach_reply tool. `reply` is \
the short, warm message the kid sees. `ladder_level` is your honest read \
of which level above this reply is. `asked_for_answer` is true only if \
the kid's latest message asked you to just give the answer.
{session_state}

--- The problem the kid is solving ---
{statement}

--- The answer and worked solution (FOR YOUR CONTEXT ONLY — never reveal, \
quote, or confirm any of this to the kid) ---
Answer: {answer}

{solution}
"""


def _build_system_prompt(
    *,
    statement: str,
    answer: str,
    solution: str,
    current_ladder_level: int,
    consecutive_asked_for_answer_count: int,
) -> str:
    session_state = f"\nCurrent nudge level so far this session: {current_ladder_level}."
    if consecutive_asked_for_answer_count >= 2:
        session_state += (
            " The kid has now asked for the answer more than once in a row. "
            "Kindly name that out loud before redirecting again — don't pretend not to notice."
        )
    return _SYSTEM_PROMPT_TEMPLATE.format(
        session_state=session_state,
        statement=statement.strip() or "(no statement)",
        answer=answer.strip() or "(no answer on file)",
        solution=solution.strip() or "(no worked solution on file)",
    )


def _ends_in_nudge(reply: str) -> bool:
    return reply.strip().endswith("?")


def _repair_missing_nudge(reply: str) -> str:
    if _ends_in_nudge(reply):
        return reply
    return f"{reply.rstrip()} What could you try next?"


_INT_RE = re.compile(r"-?\d[\d,]*")


def _reveals_answer(reply: str, answer: str, kind: MathAnswerKind) -> bool:
    """Catches the coach stating the bare answer value — the fact-leak
    guard can't (its 6-word floor and 25-char match miss a short number).
    For integer answers this can occasionally over-trigger if the answer
    value legitimately appears in a hint; that fails safe (the reply is
    swapped for a redirect), an accepted v1 tradeoff mirroring the
    fact-leak guard's own documented bluntness."""
    if kind == MathAnswerKind.integer:
        try:
            target = int(answer.strip().replace(",", ""))
        except ValueError:
            return False
        for match in _INT_RE.findall(reply):
            try:
                if int(match.replace(",", "")) == target:
                    return True
            except ValueError:
                continue
        return False
    normalized_answer = " ".join(answer.strip().casefold().split())
    return bool(normalized_answer) and normalized_answer in " ".join(reply.casefold().split())


async def _session_state(
    db: AsyncSession, problem_id: uuid.UUID, user_id: uuid.UUID, session_id: uuid.UUID
) -> tuple[list[MathCoachMessage], int, int]:
    result = await db.execute(
        select(MathCoachMessage)
        .where(
            MathCoachMessage.math_problem_id == problem_id,
            MathCoachMessage.user_id == user_id,
            MathCoachMessage.session_id == session_id,
        )
        .order_by(MathCoachMessage.created_at)
    )
    session_messages = list(result.scalars().all())

    assistant_messages = [m for m in session_messages if m.role == MathCoachMessageRole.assistant]
    current_ladder_level = assistant_messages[-1].ladder_level if assistant_messages else 1

    consecutive_asked_for_answer_count = 0
    for message in reversed(assistant_messages):
        if message.asked_for_answer:
            consecutive_asked_for_answer_count += 1
        else:
            break

    return session_messages, (current_ladder_level or 1), consecutive_asked_for_answer_count


def _to_anthropic_messages(session_messages: list[MathCoachMessage]) -> list[dict[str, str]]:
    return [{"role": m.role.value, "content": m.body} for m in session_messages]


async def list_messages(db: AsyncSession, problem: MathProblem) -> list[MathCoachMessage]:
    result = await db.execute(
        select(MathCoachMessage)
        .where(MathCoachMessage.math_problem_id == problem.id)
        .order_by(MathCoachMessage.created_at)
    )
    return list(result.scalars().all())


async def send_message(
    db: AsyncSession,
    current_user: User,
    problem: MathProblem,
    session_id: uuid.UUID,
    user_text: str,
) -> MathCoachMessage:
    # Persist the kid's own words before ever calling the LLM — never lose
    # them to an API failure.
    user_message = MathCoachMessage(
        id=uuid.uuid4(),
        math_problem_id=problem.id,
        user_id=current_user.id,
        session_id=session_id,
        role=MathCoachMessageRole.user,
        body=user_text,
    )
    db.add(user_message)
    await db.commit()
    await db.refresh(user_message)

    session_messages, current_ladder_level, consecutive_asked_for_answer_count = await _session_state(
        db, problem.id, current_user.id, session_id
    )

    if len(session_messages) > _MAX_MESSAGES_PER_SESSION:
        return await _persist_assistant_reply(
            db,
            problem=problem,
            user_id=current_user.id,
            session_id=session_id,
            reply=_SESSION_CAP_REPLY,
            ladder_level=current_ladder_level,
            asked_for_answer=False,
            answer_leak_blocked=False,
            is_fallback=True,
        )

    # Everything from prompt assembly through the leak/repair steps is
    # wrapped in one broad handler: the kid must never see a raw error, and
    # a bug in the leak logic must never let a raw model reply through.
    try:
        system_prompt = _build_system_prompt(
            statement=problem.statement_markdown,
            answer=problem.answer,
            solution=problem.solution_markdown,
            current_ladder_level=current_ladder_level,
            consecutive_asked_for_answer_count=consecutive_asked_for_answer_count,
        )
        tool_input = await anthropic_client.send_structured(
            system=system_prompt,
            messages=_to_anthropic_messages(session_messages),
            tool=_SUBMIT_COACH_REPLY_TOOL,
        )
        reply = str(tool_input["reply"])
        ladder_level = int(tool_input.get("ladder_level", current_ladder_level))
        asked_for_answer = bool(tool_input.get("asked_for_answer", False))

        # De-escalate freely; escalate at most one rung per turn.
        ladder_level = max(1, min(ladder_level, current_ladder_level + 1, 4))

        answer_leak_blocked = is_fact_leak(reply, problem.solution_markdown) or _reveals_answer(
            reply, problem.answer, problem.answer_kind
        )
        if answer_leak_blocked:
            reply = _ANSWER_LEAK_REPLY
        else:
            reply = _repair_missing_nudge(reply)
    except Exception:
        _logger.exception(
            "Maths coach reply failed for problem_id=%s session_id=%s", problem.id, session_id
        )
        return await _persist_assistant_reply(
            db,
            problem=problem,
            user_id=current_user.id,
            session_id=session_id,
            reply=_API_FAILURE_REPLY,
            ladder_level=current_ladder_level,
            asked_for_answer=False,
            answer_leak_blocked=False,
            is_fallback=True,
        )

    return await _persist_assistant_reply(
        db,
        problem=problem,
        user_id=current_user.id,
        session_id=session_id,
        reply=reply,
        ladder_level=ladder_level,
        asked_for_answer=asked_for_answer,
        answer_leak_blocked=answer_leak_blocked,
        is_fallback=False,
    )


async def _persist_assistant_reply(
    db: AsyncSession,
    *,
    problem: MathProblem,
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    reply: str,
    ladder_level: int,
    asked_for_answer: bool,
    answer_leak_blocked: bool,
    is_fallback: bool,
) -> MathCoachMessage:
    assistant_message = MathCoachMessage(
        id=uuid.uuid4(),
        math_problem_id=problem.id,
        user_id=user_id,
        session_id=session_id,
        role=MathCoachMessageRole.assistant,
        body=reply,
        ladder_level=ladder_level,
        asked_for_answer=asked_for_answer,
        answer_leak_blocked=answer_leak_blocked,
        is_fallback=is_fallback,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)
    return assistant_message
