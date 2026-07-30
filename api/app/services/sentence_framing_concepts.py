from dataclasses import dataclass

# Narrow v1 set, same "start narrow" precedent as spelling_service's
# homophone list and grammar_concepts.py's four concepts. Unlike
# grammar_concepts.py, this content is never sent to an LLM — detection
# for both concepts below is 100% local/rule-based (see
# sentence_framing_service.py) — the rule/examples here are purely the
# kid-facing hint.


@dataclass(frozen=True)
class ExamplePair:
    incorrect: str
    correct: str


@dataclass(frozen=True)
class Concept:
    id: str
    label: str
    rule: str
    examples: list[ExamplePair]


_CONCEPT_LIST: list[Concept] = [
    Concept(
        id="repeated_sentence_openings",
        label="Varying your sentence openings",
        rule=(
            "If a few sentences in a row start the same way, try opening one of them "
            "differently — with a time word, a place, or an action."
        ),
        examples=[
            ExamplePair(
                "I went to the park. I saw a dog. I threw a ball.",
                "I went to the park. There, I saw a dog. Excited, I threw a ball.",
            ),
        ],
    ),
    Concept(
        id="choppy_short_sentences",
        label="Combining short sentences",
        rule="A few very short sentences in a row can feel choppy — try joining two together or adding a detail.",
        examples=[
            ExamplePair("The dog ran. It was fast. I laughed.", "The dog ran fast, and I laughed."),
        ],
    ),
]

CONCEPTS: dict[str, Concept] = {concept.id: concept for concept in _CONCEPT_LIST}

# How-To style legitimately uses short imperative steps ("Cut the paper.
# Fold it in half.") — that's good instructional writing, not a craft
# problem, so it's dropped from the active set deterministically rather
# than trusted to a prompt (same pattern as Grammar's diary_entry skip,
# just with no LLM to instruct in the first place).
_CHOPPY_ID = "choppy_short_sentences"
_STYLES_EXEMPT_FROM_CHOPPY_CHECK = {"how_to"}


def active_concepts_for_style(style: str | None) -> list[Concept]:
    if style in _STYLES_EXEMPT_FROM_CHOPPY_CHECK:
        return [c for c in _CONCEPT_LIST if c.id != _CHOPPY_ID]
    return list(_CONCEPT_LIST)
