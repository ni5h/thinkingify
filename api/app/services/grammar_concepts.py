from dataclasses import dataclass

# Narrow v1 set, matching how Spelling started with ~15 homophone pairs
# rather than trying to cover everything. Each concept's rule + examples
# serve double duty: they're both the Socratic hint shown to the kid *and*
# the few-shot grounding embedded in the LLM's detection prompt — one
# source of truth, not two. The LLM only ever classifies against this
# content; it never writes the rule or the examples itself.


@dataclass(frozen=True)
class ExamplePair:
    incorrect: str
    correct: str


@dataclass(frozen=True)
class GrammarConcept:
    id: str
    label: str
    rule: str
    examples: list[ExamplePair]


_CONCEPT_LIST: list[GrammarConcept] = [
    GrammarConcept(
        id="subject_verb_agreement",
        label="Subject and verb agreement",
        rule="The subject and the verb need to match — one dog runs, two dogs run.",
        examples=[
            ExamplePair("The dogs runs across the yard.", "The dogs run across the yard."),
            ExamplePair("She go to school every day.", "She goes to school every day."),
        ],
    ),
    GrammarConcept(
        id="run_on_sentence",
        label="Run-on sentences",
        rule="If you have two full sentences stuck together, split them with a period or add a joining word.",
        examples=[
            ExamplePair("The rain started we ran inside.", "The rain started, so we ran inside."),
            ExamplePair("I like dogs I like cats too.", "I like dogs. I like cats too."),
        ],
    ),
    GrammarConcept(
        id="sentence_fragment",
        label="Sentence fragments",
        rule="Every sentence needs both a subject (who or what) and a verb (what they're doing).",
        examples=[
            ExamplePair("Running through the forest.", "The fox was running through the forest."),
            ExamplePair("Because it was raining.", "We stayed inside because it was raining."),
        ],
    ),
    GrammarConcept(
        id="tense_consistency",
        label="Staying in one tense",
        rule="Try to stay in one time — past or present — unless you're switching on purpose.",
        examples=[
            ExamplePair(
                "She walked to the store and buys some milk.", "She walked to the store and bought some milk."
            ),
            ExamplePair("He opens the door and saw a cat.", "He opened the door and saw a cat."),
        ],
    ),
]

CONCEPTS: dict[str, GrammarConcept] = {concept.id: concept for concept in _CONCEPT_LIST}

# Diary Entry legitimately mixes past narration with present-tense
# reflection — this is a deliberate, deterministic drop from the active
# set (not just a prompt instruction), so it can't be forgotten by the model.
_TENSE_CONSISTENCY_ID = "tense_consistency"
_STYLES_EXEMPT_FROM_TENSE_CHECK = {"diary_entry"}


def active_concepts_for_style(style: str | None) -> list[GrammarConcept]:
    if style in _STYLES_EXEMPT_FROM_TENSE_CHECK:
        return [c for c in _CONCEPT_LIST if c.id != _TENSE_CONSISTENCY_ID]
    return list(_CONCEPT_LIST)
