"""Mechanical backstop for the companion's "never states a topic fact"
hard rule — see api/app/services/companion_service.py.

Catches verbatim/near-verbatim recitation of source text (a topic's
explainer_markdown/audio_transcript) only. A fact restated in genuinely
different words is real, unaddressed residual risk that no cheap
text-matching check can see — this is a deliberate, honest limitation,
not an oversight. Thresholds below are reasonable starting points, not
tuned against real model output; expect to adjust them during
verification (see the plan's fact-leak backstop step).
"""

import difflib
import re

_SHINGLE_SIZE = 7
_MIN_REPLY_WORDS_FOR_CHECK = 6
_LONGEST_MATCH_MIN_CHARS = 25
_LONGEST_MATCH_MIN_FRACTION = 0.35


def _normalize_words(text: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", text.lower())


def _shingles(words: list[str], size: int) -> set[tuple[str, ...]]:
    if len(words) < size:
        return set()
    return {tuple(words[i : i + size]) for i in range(len(words) - size + 1)}


def _has_shingle_overlap(reply_words: list[str], source_words: list[str]) -> bool:
    reply_shingles = _shingles(reply_words, _SHINGLE_SIZE)
    if not reply_shingles:
        return False
    return bool(reply_shingles & _shingles(source_words, _SHINGLE_SIZE))


def _has_long_contiguous_match(reply_lower: str, source_lower: str) -> bool:
    matcher = difflib.SequenceMatcher(None, reply_lower, source_lower, autojunk=False)
    match = matcher.find_longest_match(0, len(reply_lower), 0, len(source_lower))
    if match.size < _LONGEST_MATCH_MIN_CHARS:
        return False
    return (match.size / len(reply_lower)) >= _LONGEST_MATCH_MIN_FRACTION


def is_fact_leak(reply: str, *source_texts: str | None) -> bool:
    """True if `reply` looks like verbatim/near-verbatim recitation of any
    non-empty text in `source_texts`."""
    reply_words = _normalize_words(reply)
    if len(reply_words) < _MIN_REPLY_WORDS_FOR_CHECK:
        return False
    reply_lower = reply.lower()

    for source in source_texts:
        if not source:
            continue
        source_words = _normalize_words(source)
        if _has_shingle_overlap(reply_words, source_words):
            return True
        if _has_long_contiguous_match(reply_lower, source.lower()):
            return True

    return False
