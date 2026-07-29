import logging
import re
import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from spellchecker import SpellChecker

from app.models.content import Content
from app.models.spelling_flag import SpellingErrorType, SpellingFlag, SpellingFlagStatus
from app.models.topic import Topic
from app.services import anthropic_client, topic_service
from app.services.anthropic_client import AnthropicClientError

_logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[A-Za-z']+")
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_MARKDOWN_STRIP_RE = re.compile(r"[#*_`\[\]()>~]")

# Small, fixed set of homophone groups a 9-year-old writer commonly mixes
# up. Detection for these is the one place the LLM is used — a dictionary
# can't tell "their" from "there" apart, both are real words; only
# sentence-level context can.
_HOMOPHONE_GROUPS: list[set[str]] = [
    {"their", "there", "they're"},
    {"your", "you're"},
    {"its", "it's"},
    {"to", "too", "two"},
    {"here", "hear"},
    {"write", "right"},
    {"know", "no"},
    {"break", "brake"},
    {"bear", "bare"},
    {"sea", "see"},
    {"whole", "hole"},
    {"week", "weak"},
    {"wear", "where"},
    {"threw", "through"},
    {"for", "four"},
]
_HOMOPHONE_WORDS: set[str] = {word for group in _HOMOPHONE_GROUPS for word in group}
_MAX_HOMOPHONE_ITEMS_PER_CHECK = 20

_SUBMIT_HOMOPHONE_JUDGMENTS_TOOL = {
    "name": "submit_homophone_judgments",
    "description": "Submit your judgment for each numbered sentence.",
    "input_schema": {
        "type": "object",
        "properties": {
            "judgments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "index": {"type": "integer", "description": "The item number this judgment is for."},
                        "correct": {
                            "type": "boolean",
                            "description": "True if the flagged word is used correctly in this sentence.",
                        },
                        "suggested_word": {
                            "type": "string",
                            "description": "The word that best fits this sentence (same as the flagged word if correct).",
                        },
                        "reason": {
                            "type": "string",
                            "description": "One short, kid-friendly sentence explaining the difference (e.g. what each word means).",
                        },
                    },
                    "required": ["index", "correct", "suggested_word", "reason"],
                },
            }
        },
        "required": ["judgments"],
    },
}

_HOMOPHONE_SYSTEM_PROMPT = """\
You are checking a child's (around 9 years old) writing for mixed-up \
homophones (words that sound alike but mean different things, like \
"their"/"there"/"they're"). For each numbered sentence below, decide \
whether the bolded word is the right word for that sentence's meaning. \
If it's wrong, say which word from the same homophone family fits \
instead, and explain the difference in one short, simple, kid-friendly \
sentence (e.g. "there" is a place, "their" means something belongs to \
them). Always call submit_homophone_judgments with one judgment per \
numbered item, in the same order.\
"""


def _tokenize(text: str) -> list[str]:
    return [w.strip("'") for w in _WORD_RE.findall(text) if w.strip("'")]


def _split_sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(text.strip()) if s.strip()]


def _sentence_for_word(sentences: list[str], word: str) -> str:
    lw = word.lower()
    for sentence in sentences:
        if lw in {t.lower() for t in _tokenize(sentence)}:
            return sentence
    return word


def _topic_vocabulary(topic: Topic | None) -> list[str]:
    if topic is None:
        return []
    stripped = _MARKDOWN_STRIP_RE.sub(" ", topic.explainer_markdown)
    return list({w.lower() for w in _tokenize(stripped)})


def _build_checker(topic: Topic | None) -> SpellChecker:
    checker = SpellChecker()
    topic_words = _topic_vocabulary(topic)
    if topic_words:
        checker.word_frequency.load_words(topic_words)
    return checker


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = curr
    return prev[-1]


def _best_suggestion(checker: SpellChecker, word: str) -> str | None:
    """pyspellchecker's own `.correction()` picks a raw top-1 candidate by
    corpus frequency alone, which can occasionally suggest a real but
    unrelated word for a badly mangled attempt at a longer/rarer word.
    Filtering the full candidate set to those within +/-2 characters of the
    original word's length, then ranking by edit distance first and
    frequency only as a tiebreak, meaningfully reduces the chance of
    confidently "fixing" a word into something the kid didn't mean.
    """
    candidates = checker.candidates(word)
    if not candidates:
        return None
    filtered = [c for c in candidates if abs(len(c) - len(word)) <= 2] or list(candidates)
    filtered.sort(key=lambda c: (_levenshtein(word, c), -checker.word_frequency[c]))
    return filtered[0]


_GENERIC_HINT = "Sound it out slowly, one syllable at a time — one part of this word isn't quite right yet."


def _classify_hint(word: str, suggestion: str | None) -> str:
    if not suggestion or suggestion.lower() == word.lower():
        return _GENERIC_HINT
    w, s = word.lower(), suggestion.lower()

    if w.replace("ie", "ei", 1) == s or w.replace("ei", "ie", 1) == s:
        return 'Remember: "i before e, except after c" — check the order of those two letters.'

    if abs(len(w) - len(s)) == 1:
        longer, shorter = (s, w) if len(s) > len(w) else (w, s)
        for i in range(len(longer)):
            if longer[:i] + longer[i + 1 :] == shorter:
                if longer[i] == "e":
                    return 'This word has a silent "e" — check whether it belongs at the end.'
                if i > 0 and longer[i] == longer[i - 1]:
                    return "Listen closely — is one of the letters in the middle doubled up?"
    return _GENERIC_HINT


async def _existing_flags_by_word(db: AsyncSession, content_id: uuid.UUID) -> dict[str, SpellingFlag]:
    result = await db.execute(select(SpellingFlag).where(SpellingFlag.content_id == content_id))
    return {flag.word: flag for flag in result.scalars().all()}


def _upsert(
    db: AsyncSession,
    existing_by_word: dict[str, SpellingFlag],
    *,
    content_id: uuid.UUID,
    word: str,
    error_type: SpellingErrorType,
    context_sentence: str,
    suggested_correction: str | None,
    hint: str | None,
) -> SpellingFlag:
    existing = existing_by_word.get(word)
    if existing is None:
        flag = SpellingFlag(
            id=uuid.uuid4(),
            content_id=content_id,
            word=word,
            error_type=error_type,
            context_sentence=context_sentence,
            suggested_correction=suggested_correction,
            hint=hint,
            status=SpellingFlagStatus.pending,
        )
        db.add(flag)
        existing_by_word[word] = flag
        return flag

    existing.error_type = error_type
    existing.context_sentence = context_sentence
    existing.suggested_correction = suggested_correction
    existing.hint = hint
    if existing.status == SpellingFlagStatus.self_corrected:
        # The same word is freshly misspelled again elsewhere — a
        # legitimate new mistake, since a confirmed fix always replaces
        # every prior occurrence, so reappearance can only mean a fresh
        # instance of the typo.
        existing.status = SpellingFlagStatus.pending
        existing.attempt_count = 0
        existing.hint_revealed = False
        existing.resolved_at = None
    return existing


async def _topic_for_content(db: AsyncSession, content: Content) -> Topic | None:
    if content.topic_id is None:
        return None
    return await topic_service.get_by_id(db, content.topic_id)


async def run_check(db: AsyncSession, content: Content, text: str) -> list[SpellingFlag]:
    topic = await _topic_for_content(db, content)
    sentences = _split_sentences(text)
    all_words = [w for sentence in sentences for w in _tokenize(sentence)]

    existing_by_word = await _existing_flags_by_word(db, content.id)
    kept_words = {w for w, f in existing_by_word.items() if f.status == SpellingFlagStatus.kept_as_is}

    checker = _build_checker(topic)
    candidate_words = {w.lower() for w in all_words} - kept_words
    unknown = checker.unknown(candidate_words) if candidate_words else set()
    for word in unknown:
        suggestion = _best_suggestion(checker, word)
        _upsert(
            db,
            existing_by_word,
            content_id=content.id,
            word=word,
            error_type=SpellingErrorType.misspelling,
            context_sentence=_sentence_for_word(sentences, word),
            suggested_correction=suggestion,
            hint=_classify_hint(word, suggestion),
        )

    homophone_items: list[tuple[str, str]] = []
    seen_homophone_words: set[str] = set()
    for sentence in sentences:
        for token in _tokenize(sentence):
            lw = token.lower()
            if lw in _HOMOPHONE_WORDS and lw not in kept_words and lw not in seen_homophone_words:
                seen_homophone_words.add(lw)
                homophone_items.append((lw, sentence))
                if len(homophone_items) >= _MAX_HOMOPHONE_ITEMS_PER_CHECK:
                    break
        if len(homophone_items) >= _MAX_HOMOPHONE_ITEMS_PER_CHECK:
            break

    if homophone_items:
        judgments = await _judge_homophones(homophone_items)
        for (word, sentence), judgment in zip(homophone_items, judgments):
            if judgment is None or judgment.get("correct", True):
                continue
            _upsert(
                db,
                existing_by_word,
                content_id=content.id,
                word=word,
                error_type=SpellingErrorType.homophone,
                context_sentence=sentence,
                suggested_correction=str(judgment.get("suggested_word") or "").strip() or None,
                hint=str(judgment.get("reason") or "").strip() or None,
            )

    await db.commit()
    return await list_pending(db, content)


async def _judge_homophones(items: list[tuple[str, str]]) -> list[dict | None]:
    lines = "\n".join(f'{i + 1}. "{sentence}" (flagged word: {word})' for i, (word, sentence) in enumerate(items))
    try:
        tool_input = await anthropic_client.send_structured(
            system=_HOMOPHONE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": lines}],
            tool=_SUBMIT_HOMOPHONE_JUDGMENTS_TOOL,
        )
    except AnthropicClientError:
        _logger.exception("Homophone check failed, skipping this pass")
        return [None] * len(items)

    judgments = tool_input.get("judgments")
    if not isinstance(judgments, list):
        return [None] * len(items)

    by_index: dict[int, dict] = {}
    for entry in judgments:
        if isinstance(entry, dict) and isinstance(entry.get("index"), int):
            by_index[entry["index"]] = entry
    return [by_index.get(i + 1) for i in range(len(items))]


def _substitute_word(sentence: str, old_word: str, new_word: str) -> str:
    return re.sub(rf"\b{re.escape(old_word)}\b", new_word, sentence, flags=re.IGNORECASE)


async def _judge_single_homophone(sentence: str, old_word: str, attempt_word: str) -> bool:
    substituted = _substitute_word(sentence, old_word, attempt_word)
    judgments = await _judge_homophones([(attempt_word, substituted)])
    judgment = judgments[0]
    if judgment is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not check that just now — try again in a moment.",
        )
    return bool(judgment.get("correct", False))


async def get_flag(db: AsyncSession, flag_id: uuid.UUID) -> SpellingFlag | None:
    result = await db.execute(select(SpellingFlag).where(SpellingFlag.id == flag_id))
    return result.scalar_one_or_none()


async def list_pending(db: AsyncSession, content: Content) -> list[SpellingFlag]:
    result = await db.execute(
        select(SpellingFlag)
        .where(SpellingFlag.content_id == content.id, SpellingFlag.status == SpellingFlagStatus.pending)
        .order_by(SpellingFlag.created_at)
    )
    return list(result.scalars().all())


async def attempt_fix(db: AsyncSession, content: Content, flag: SpellingFlag, attempt_word: str) -> SpellingFlag:
    attempt_word = attempt_word.strip()

    if flag.error_type == SpellingErrorType.misspelling:
        topic = await _topic_for_content(db, content)
        checker = _build_checker(topic)
        is_correct = len(checker.unknown([attempt_word.lower()])) == 0
    else:
        is_correct = await _judge_single_homophone(flag.context_sentence, flag.word, attempt_word)

    if is_correct:
        flag.status = SpellingFlagStatus.self_corrected
        flag.resolved_at = datetime.now(UTC)
    else:
        flag.attempt_count += 1
        if flag.attempt_count >= 3:
            flag.hint_revealed = True

    await db.commit()
    await db.refresh(flag)
    return flag


async def override(db: AsyncSession, flag: SpellingFlag) -> SpellingFlag:
    if flag.attempt_count < 2:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Try a couple of guesses first.",
        )
    flag.status = SpellingFlagStatus.kept_as_is
    flag.resolved_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(flag)
    return flag
