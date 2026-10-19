"""Selects adapters by config. One place to map a name → implementation, so the
pipeline code never branches on provider."""
from __future__ import annotations

from app.core.config import settings
from app.pipeline.adapters.base import EmbeddingAdapter, ImageAdapter, TextAdapter, TTSAdapter
from app.pipeline.adapters.embeddings import HashEmbeddingAdapter, LocalEmbeddingAdapter
from app.pipeline.adapters.image import StubImageAdapter
from app.pipeline.adapters.text import ClaudeTextAdapter, StubTextAdapter
from app.pipeline.adapters.tts import StubTTSAdapter

_TEXT = {"claude": ClaudeTextAdapter, "stub": StubTextAdapter}
_EMBED = {"local": LocalEmbeddingAdapter, "hash": HashEmbeddingAdapter}
_IMAGE = {"stub": StubImageAdapter}
_TTS = {"stub": StubTTSAdapter}


def _select(table: dict, key: str, label: str):
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"Unknown {label} adapter {key!r}; choose from {sorted(table)}") from None


def get_text_adapter(*, model: str | None = None) -> TextAdapter:
    return _select(_TEXT, settings.pipeline_text_adapter, "text")(model=model)


def get_generation_adapter() -> TextAdapter:
    return get_text_adapter(model=settings.pipeline_generation_model or None)


def get_critique_adapter() -> TextAdapter:
    return get_text_adapter(model=settings.pipeline_critique_model or None)


def get_embedding_adapter() -> EmbeddingAdapter:
    return _select(_EMBED, settings.pipeline_embedding_adapter, "embedding")()


def get_image_adapter() -> ImageAdapter:
    return _select(_IMAGE, settings.pipeline_image_adapter, "image")()


def get_tts_adapter() -> TTSAdapter:
    return _select(_TTS, settings.pipeline_tts_adapter, "tts")()
