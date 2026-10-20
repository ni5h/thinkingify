"""Selects adapters by config. One place to map a name → implementation, so the
pipeline code never branches on provider."""
from __future__ import annotations

from app.core.config import settings
from app.pipeline.adapters.base import EmbeddingAdapter, ImageAdapter, TextAdapter, TTSAdapter
from app.pipeline.adapters.embeddings import HashEmbeddingAdapter, LocalEmbeddingAdapter
from app.pipeline.adapters.image import ClaudeSvgImageAdapter, StubImageAdapter
from app.pipeline.adapters.text import ClaudeTextAdapter, StubTextAdapter
from app.pipeline.adapters.tts import StubTTSAdapter

_TEXT = {"claude": ClaudeTextAdapter, "stub": StubTextAdapter}
_EMBED = {"local": LocalEmbeddingAdapter, "hash": HashEmbeddingAdapter}
_IMAGE = {"stub": StubImageAdapter, "svg": ClaudeSvgImageAdapter}
_TTS = {"stub": StubTTSAdapter}


def _select(table: dict, key: str, label: str):
    try:
        return table[key]
    except KeyError:
        raise ValueError(f"Unknown {label} adapter {key!r}; choose from {sorted(table)}") from None


_GEN_TIMEOUT = 120.0  # a full card session takes longer than a chat reply


def get_text_adapter(*, model: str | None = None, max_tokens: int = 1024, timeout: float | None = None) -> TextAdapter:
    return _select(_TEXT, settings.pipeline_text_adapter, "text")(model=model, max_tokens=max_tokens, timeout=timeout)


def get_generation_adapter() -> TextAdapter:
    # A full card session / item set is large — give generation room (tokens)
    # and time so the structured reply isn't truncated or timed out.
    return get_text_adapter(model=settings.pipeline_generation_model or None, max_tokens=4096, timeout=_GEN_TIMEOUT)


def get_critique_adapter() -> TextAdapter:
    return get_text_adapter(model=settings.pipeline_critique_model or None)


def get_embedding_adapter() -> EmbeddingAdapter:
    return _select(_EMBED, settings.pipeline_embedding_adapter, "embedding")()


def get_image_adapter() -> ImageAdapter:
    return _select(_IMAGE, settings.pipeline_image_adapter, "image")()


def get_tts_adapter() -> TTSAdapter:
    return _select(_TTS, settings.pipeline_tts_adapter, "tts")()
