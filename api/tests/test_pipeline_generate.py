import uuid

from app.pipeline.adapters.base import ImageResult
from app.pipeline.generate import generate_session


class SpyText:
    name = "spy"

    def __init__(self, responses):
        self.responses = responses
        self.prompts: list[str] = []
        self.systems: list[str] = []

    async def generate(self, *, system, prompt, tool):
        self.prompts.append(prompt)
        self.systems.append(system)
        return self.responses[tool["name"]]


class StubImg:
    name = "stub"

    async def generate(self, brief):
        return ImageResult(brief=brief, url=None, placeholder=True)


CARD_RESP = {
    "title": "Place value",
    "cards": [
        {
            "title": "Houses",
            "text": "Each digit lives in a house.",
            "visual_brief": "four houses in a row",
            "audio_script": "Think about what happens when a house gets ten.",
            "think_q": "Which house?",
            "think_options": ["Tens", "Ones"],
            "think_answer_index": 0,
            "think_why": "count from the right",
        }
    ],
    "recap_lines": ["A digit's worth depends on its house."],
    "remember": "The house decides the worth.",
}
ITEMS_RESP = {
    "items": [
        {
            "body": "In 45, what is the 4 worth?",
            "options": ["40", "4"],
            "answer": "40",
            "hint": "tens",
            "difficulty": 1,
            "source_card_index": 0,
        }
    ]
}


async def test_maths_items_are_code_generated_with_no_items_model_call():
    spy = SpyText({"card_session": CARD_RESP})
    session = await generate_session(
        concept_id=str(uuid.uuid4()),
        title="Place value",
        subject_code="maths",
        text_adapter=spy,
        image_adapter=StubImg(),
        band=2,
        seed=5,
    )
    assert session.items and all(it.template_id for it in session.items)
    assert len(spy.prompts) == 1  # only the card call; items came from code


async def test_evs_items_come_from_the_model():
    spy = SpyText({"card_session": CARD_RESP, "check_items": ITEMS_RESP})
    session = await generate_session(
        concept_id=str(uuid.uuid4()),
        title="Our Food",
        subject_code="evs",
        text_adapter=spy,
        image_adapter=StubImg(),
        band=2,
    )
    assert len(spy.prompts) == 2
    assert session.items and session.items[0].template_id is None
    assert session.items[0].source_card_index == 0


async def test_card_prompt_uses_only_concept_metadata():
    spy = SpyText({"card_session": CARD_RESP})
    await generate_session(
        concept_id="x",
        title="Place value",
        subject_code="maths",
        text_adapter=spy,
        image_adapter=StubImg(),
        band=2,
        description="digits and houses",
    )
    assert "Place value" in spy.prompts[0]
    assert "digits and houses" in spy.prompts[0]
