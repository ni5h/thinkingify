import uuid

from sqlalchemy import select

from app.core.config import settings
from app.models.curriculum import Asset, AssetKind, Chapter, Concept, Item, Subject
from app.pipeline import run as run_mod
from app.pipeline.adapters.base import ImageResult
from app.pipeline.adapters.embeddings import HashEmbeddingAdapter

SECRET = "ZZZ_SECRET_REFERENCE_PASSAGE_DO_NOT_LEAK"


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

    def generate(self, brief):
        return ImageResult(brief=brief, url=None, placeholder=True)


class FakeCritique:
    name = "crit"

    def __init__(self):
        self.prompts: list[str] = []

    async def generate(self, *, system, prompt, tool):
        self.prompts.append(prompt)
        return {"correct_option_indices": [0]}  # option 0 is correct


CARDS = {
    "title": "Our Food",
    "cards": [
        {
            "title": "Food from plants",
            "text": "Many foods come from plants.",
            "visual_brief": "a plant with fruit",
            "audio_script": "Think of a food you ate today and where it grew.",
            "think_q": "Where does rice come from?",
            "think_options": ["A plant", "A rock"],
            "think_answer_index": 0,
            "think_why": "rice is a grain from a plant",
        }
    ],
    "recap_lines": ["Food comes from plants and animals."],
    "remember": "Food has a source.",
}
# one good item (answer is option 0, matching the fake critic) and one bad item
# whose answer is not among the options — it must be rejected, never persisted.
ITEMS = {
    "items": [
        {"body": "Where does milk come from?", "options": ["A cow", "A tree"], "answer": "A cow", "hint": "an animal", "difficulty": 1, "source_card_index": 0},
        {"body": "Where does an apple grow?", "options": ["A tree", "A river"], "answer": "The sky", "hint": "a plant", "difficulty": 1, "source_card_index": 0},
    ]
}


async def _make_concept(db) -> Concept:
    subject = Subject(id=uuid.uuid4(), name="EVS", code="evs", grade=4)
    db.add(subject)
    await db.flush()
    chapter = Chapter(id=uuid.uuid4(), subject_id=subject.id, title="Our Food", order_index=0)
    db.add(chapter)
    await db.flush()
    concept = Concept(id=uuid.uuid4(), chapter_id=chapter.id, title="Where food comes from", order_index=0)
    db.add(concept)
    await db.commit()
    return concept


async def test_failed_prechecks_never_persist_and_reference_never_prompted(db, tmp_path, monkeypatch):
    # A private reference file on disk — used only for local dedupe embedding.
    (tmp_path / "ref.txt").write_text(SECRET + " some olympiad passage here", encoding="utf-8")
    monkeypatch.setattr(settings, "reference_dir", str(tmp_path))
    monkeypatch.setattr(settings, "pipeline_reading_grade_max", 8.0)

    gen = SpyText({"card_session": CARDS, "check_items": ITEMS})
    crit = FakeCritique()
    monkeypatch.setattr(run_mod, "get_generation_adapter", lambda: gen)
    monkeypatch.setattr(run_mod, "get_critique_adapter", lambda: crit)
    monkeypatch.setattr(run_mod, "get_image_adapter", lambda: StubImg())
    monkeypatch.setattr(run_mod, "get_embedding_adapter", lambda: HashEmbeddingAdapter())

    concept = await _make_concept(db)
    result = await run_mod.build_concept(
        db, concept_id=str(concept.id), title=concept.title, subject_code="evs", band=1, log=lambda _m: None
    )

    items = (await db.execute(select(Item).where(Item.concept_id == concept.id))).scalars().all()
    bodies = {i.body for i in items}
    assert "Where does milk come from?" in bodies  # good item persisted
    assert "Where does an apple grow?" not in bodies  # bad item rejected
    assert result["items_persisted"] == 1 and result["rejected"] == 1

    assets = (await db.execute(select(Asset).where(Asset.concept_id == concept.id))).scalars().all()
    assert sum(1 for a in assets if a.kind == AssetKind.card) == 1
    assert any(a.kind == AssetKind.recap for a in assets)
    assert all(a.status.value == "draft" for a in assets)

    # The reference text was embedded for dedupe but never placed in a prompt.
    blob = " ".join(gen.prompts + gen.systems + crit.prompts)
    assert SECRET not in blob
