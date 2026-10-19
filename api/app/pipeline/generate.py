"""Generate a card session for one concept.

Prompts are built only from the concept's title/description, the difficulty band
and the item kind — never from the private reference set. Cards (title, text,
visual brief, audio script, think-first question) and the recap come from the
text adapter. Check items are code-computed for maths (answers never model-set)
and model-written for EVS. Images come from the image adapter (stubbed to a
visual brief for now).
"""
from __future__ import annotations

from app.pipeline import maths
from app.pipeline.adapters.base import ImageAdapter, TextAdapter
from app.pipeline.types import GeneratedCard, GeneratedItem, GeneratedRecap, GeneratedSession

CARD_SYSTEM = (
    "You write a short Learn session for a nine-year-old in India, one concept at "
    "a time, as 5 to 7 cards. Each card holds ONE idea: a short title, one or two "
    "plain sentences, a think-first question, and an audio script. Rules: original "
    "illustrations only (describe them in the visual brief; never reference "
    "textbook art); the audio script NEVER restates the card — it refers to the "
    "card and goes further with the why, an example, or a question to think about "
    "before tapping next. Calm, encouraging tone. No scores, no streaks."
)

ITEMS_SYSTEM = (
    "You write 4 to 5 quick-check questions for a nine-year-old in India about one "
    "concept. Each has one clearly correct answer, a few plausible options, a "
    "one-line hint, a difficulty from 1 (easiest) to 5, and the index of the card "
    "it came from. Age-appropriate, Indian context, calm tone."
)

CARD_TOOL = {
    "name": "card_session",
    "description": "A Learn card session for one concept.",
    "input_schema": {
        "type": "object",
        "required": ["title", "cards", "recap_lines", "remember"],
        "properties": {
            "title": {"type": "string"},
            "cards": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["title", "text", "visual_brief", "audio_script", "think_q", "think_options", "think_answer_index", "think_why"],
                    "properties": {
                        "title": {"type": "string"},
                        "text": {"type": "string"},
                        "visual_brief": {"type": "string"},
                        "audio_script": {"type": "string"},
                        "think_q": {"type": "string"},
                        "think_options": {"type": "array", "items": {"type": "string"}},
                        "think_answer_index": {"type": "integer"},
                        "think_why": {"type": "string"},
                    },
                },
            },
            "recap_lines": {"type": "array", "items": {"type": "string"}},
            "remember": {"type": "string"},
        },
    },
}

ITEMS_TOOL = {
    "name": "check_items",
    "description": "Quick-check questions for one concept.",
    "input_schema": {
        "type": "object",
        "required": ["items"],
        "properties": {
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["body", "options", "answer", "hint", "difficulty", "source_card_index"],
                    "properties": {
                        "body": {"type": "string"},
                        "options": {"type": "array", "items": {"type": "string"}},
                        "answer": {"type": "string"},
                        "hint": {"type": "string"},
                        "difficulty": {"type": "integer"},
                        "source_card_index": {"type": "integer"},
                    },
                },
            }
        },
    },
}


def build_card_prompt(*, title: str, description: str, band: int) -> str:
    desc = f"\nConcept notes: {description}" if description else ""
    return (
        f"Concept: {title}{desc}\nDifficulty band: {band} (1 easiest, 5 hardest).\n"
        "Write the card session now."
    )


def build_items_prompt(*, title: str, cards: list[GeneratedCard], band: int) -> str:
    card_list = "\n".join(f"{i}. {c.title}" for i, c in enumerate(cards))
    return (
        f"Concept: {title}\nDifficulty band: {band}.\nCards (use the index as "
        f"source_card_index):\n{card_list}\nWrite 4 to 5 quick-check questions."
    )


def _card_from(d: dict) -> GeneratedCard:
    return GeneratedCard(
        title=d.get("title", ""),
        text=d.get("text", ""),
        visual_brief=d.get("visual_brief", ""),
        audio_script=d.get("audio_script", ""),
        think_q=d.get("think_q", ""),
        think_options=list(d.get("think_options", [])),
        think_answer_index=int(d.get("think_answer_index", 0)),
        think_why=d.get("think_why", ""),
    )


def _item_from(d: dict, n_cards: int) -> GeneratedItem:
    src = d.get("source_card_index")
    if isinstance(src, int) and not (0 <= src < n_cards):
        src = None
    return GeneratedItem(
        kind="apply",
        body=d.get("body", ""),
        options=list(d.get("options", [])),
        answer=d.get("answer", ""),
        hint=d.get("hint", ""),
        difficulty=int(d.get("difficulty", 1)),
        source_card_index=src,
    )


async def generate_session(
    *,
    concept_id: str,
    title: str,
    subject_code: str,
    text_adapter: TextAdapter,
    image_adapter: ImageAdapter,
    band: int = 2,
    description: str = "",
    seed: int | None = None,
) -> GeneratedSession:
    data = await text_adapter.generate(
        system=CARD_SYSTEM, prompt=build_card_prompt(title=title, description=description, band=band), tool=CARD_TOOL
    )
    cards = [_card_from(c) for c in data.get("cards", [])]
    for card in cards:
        result = image_adapter.generate(card.visual_brief or card.text)
        card.visual_url = result.url  # None while stubbed

    recap = GeneratedRecap(lines=list(data.get("recap_lines", [])), remember=data.get("remember", ""))

    if subject_code == "maths":
        items = maths.generate_items(band=band, n=5, seed=seed)
    else:
        idata = await text_adapter.generate(
            system=ITEMS_SYSTEM, prompt=build_items_prompt(title=title, cards=cards, band=band), tool=ITEMS_TOOL
        )
        items = [_item_from(d, len(cards)) for d in idata.get("items", [])]

    return GeneratedSession(
        concept_id=concept_id,
        subject_code=subject_code,
        title=data.get("title", title),
        cards=cards,
        recap=recap,
        items=items,
    )
