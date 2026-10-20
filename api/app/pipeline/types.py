"""In-memory shapes the pipeline passes around before anything is persisted.

Generation produces these; pre-checks filter them; only survivors are written as
`draft` rows. Keeping them as plain dataclasses (not ORM models) means a failed
item never touches the database — "failed pre-checks never reach the queue".
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GeneratedCard:
    title: str
    text: str  # one or two plain sentences
    visual_brief: str  # house-style description for the illustration
    audio_script: str  # refers to the card and goes further; never restates it
    think_q: str
    think_options: list[str]
    think_answer_index: int
    think_why: str
    visual_url: str | None = None  # set once a raster image adapter runs
    visual_svg: str | None = None  # inline SVG from the Claude-SVG adapter


@dataclass
class GeneratedRecap:
    lines: list[str]  # 3-4 recap lines
    remember: str  # one "remember" line


@dataclass
class GeneratedItem:
    kind: str  # ItemKind value (recall / apply / ...)
    body: str  # the question
    options: list[str]
    answer: str  # the correct option (verbatim, must be one of options)
    hint: str
    difficulty: int  # 1-5
    source_card_index: int | None = None
    # Maths only: the template + params so a pre-check can recompute the answer
    # in code. None for model-written (EVS) items.
    template_id: str | None = None
    params: dict = field(default_factory=dict)
    # Written by the dedupe pass.
    dedupe_score: float | None = None


@dataclass
class GeneratedSession:
    concept_id: str
    subject_code: str  # "maths" | "evs"
    title: str
    cards: list[GeneratedCard]
    recap: GeneratedRecap
    items: list[GeneratedItem]
