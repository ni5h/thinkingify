import pytest

from app.core.config import settings
from app.pipeline.adapters.embeddings import HashEmbeddingAdapter, cosine
from app.pipeline.adapters.registry import (
    get_critique_adapter,
    get_embedding_adapter,
    get_generation_adapter,
    get_image_adapter,
    get_text_adapter,
)
from app.pipeline.adapters.text import ClaudeTextAdapter, StubTextAdapter


def test_registry_selects_text_adapter_by_config(monkeypatch):
    monkeypatch.setattr(settings, "pipeline_text_adapter", "claude")
    assert isinstance(get_text_adapter(), ClaudeTextAdapter)
    monkeypatch.setattr(settings, "pipeline_text_adapter", "stub")
    assert isinstance(get_text_adapter(), StubTextAdapter)


def test_registry_rejects_unknown_adapter(monkeypatch):
    monkeypatch.setattr(settings, "pipeline_image_adapter", "midjourney")
    with pytest.raises(ValueError, match="Unknown image adapter"):
        get_image_adapter()


def test_generation_and_critique_models_resolve(monkeypatch):
    monkeypatch.setattr(settings, "pipeline_text_adapter", "claude")
    monkeypatch.setattr(settings, "pipeline_generation_model", "claude-sonnet-5")
    monkeypatch.setattr(settings, "pipeline_critique_model", "")
    gen = get_generation_adapter()
    crit = get_critique_adapter()
    assert gen._model == "claude-sonnet-5"
    # Empty critique override falls back to the app-wide model (None here).
    assert crit._model is None


def test_hash_embedding_is_deterministic_and_semantic(monkeypatch):
    monkeypatch.setattr(settings, "pipeline_embedding_adapter", "hash")
    adapter = get_embedding_adapter()
    assert isinstance(adapter, HashEmbeddingAdapter)

    v1 = adapter.embed(["the three lives in the tens house"])[0]
    v1_again = adapter.embed(["the three lives in the tens house"])[0]
    assert v1 == v1_again  # reproducible across calls

    near = adapter.embed(["the three lives in the tens house today"])[0]
    far = adapter.embed(["cats sleep on warm windowsills"])[0]
    assert cosine(v1, near) > cosine(v1, far)
    assert cosine(v1, v1_again) == pytest.approx(1.0)


def test_empty_text_embeds_to_zero_vector():
    adapter = HashEmbeddingAdapter()
    assert cosine(adapter.embed([""])[0], adapter.embed(["anything"])[0]) == 0.0


async def test_stub_text_adapter_builds_schema_shape():
    adapter = StubTextAdapter()
    tool = {
        "name": "card",
        "input_schema": {
            "type": "object",
            "required": ["title", "cards"],
            "properties": {
                "title": {"type": "string"},
                "cards": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["text", "answer_index"],
                        "properties": {
                            "text": {"type": "string"},
                            "answer_index": {"type": "integer"},
                        },
                    },
                },
            },
        },
    }
    out = await adapter.generate(system="s", prompt="p", tool=tool)
    assert set(out) == {"title", "cards"}
    assert out["cards"][0]["answer_index"] == 0
    assert isinstance(out["cards"][0]["text"], str)
