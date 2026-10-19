"""Swappable generation adapters.

One interface each for text, embeddings, images and text-to-speech, so swapping
a model or a voice changes one adapter, not the pipeline. Selected by config via
`registry.py`. Defaults are keyless (deterministic stub text, hash embeddings,
stubbed images/TTS) so tests and a fresh checkout run without any provider.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class TextAdapter(Protocol):
    """Structured (forced-tool) generation. Returns the tool input dict; the
    caller owns and validates its schema."""

    name: str

    async def generate(self, *, system: str, prompt: str, tool: dict) -> dict: ...


@runtime_checkable
class EmbeddingAdapter(Protocol):
    """Vector embeddings for dedupe. Must run locally for the private reference
    set — its text may never leave the machine."""

    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass(frozen=True)
class ImageResult:
    # Either a stored url (real provider) or a placeholder carrying the brief
    # (stub). `placeholder=True` means no image was actually generated yet.
    brief: str
    url: str | None = None
    placeholder: bool = True


@runtime_checkable
class ImageAdapter(Protocol):
    name: str

    def generate(self, brief: str) -> ImageResult: ...


@dataclass(frozen=True)
class AudioResult:
    script: str
    audio: bytes | None = None
    placeholder: bool = True


@runtime_checkable
class TTSAdapter(Protocol):
    """Text-to-speech. Runs only from a reviewed script, so it is stubbed until
    a voice is wired; the draft pipeline never calls it."""

    name: str

    def synthesize(self, script: str) -> AudioResult: ...
