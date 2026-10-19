"""Embedding adapters for dedupe.

`local` uses model2vec static embeddings — CPU-only, torch-free — so the private
reference set is embedded on the machine and its text never leaves. `hash` is a
deterministic, dependency-free fallback used by default (and in tests): same
text → same vector, shared words → higher cosine, reproducible across processes.
"""
from __future__ import annotations

import hashlib
import math
import re

from app.core.config import settings

_TOKEN = re.compile(r"[a-z0-9]+")
_HASH_DIM = 256


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class HashEmbeddingAdapter:
    name = "hash"

    def __init__(self, dim: int = _HASH_DIM) -> None:
        self._dim = dim

    def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self._dim
        for tok in _tokens(text):
            # hashlib (not builtin hash) so the bucket is stable across runs.
            bucket = int(hashlib.md5(tok.encode()).hexdigest(), 16) % self._dim
            vec[bucket] += 1.0
        norm = math.sqrt(sum(v * v for v in vec))
        if norm == 0.0:
            return vec
        return [v / norm for v in vec]


class LocalEmbeddingAdapter:
    name = "local"

    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or settings.pipeline_embedding_model
        self._model = None

    def _ensure_model(self):
        if self._model is None:
            try:
                from model2vec import StaticModel
            except ImportError as exc:  # pragma: no cover - env-specific
                raise RuntimeError(
                    "pipeline_embedding_adapter=local needs model2vec "
                    "(`pip install model2vec`). Private-reference embedding must "
                    "stay on-machine; do not switch to a hosted embeddings API."
                ) from exc
            self._model = StaticModel.from_pretrained(self._model_name)
        return self._model

    def embed(self, texts: list[str]) -> list[list[float]]:
        model = self._ensure_model()
        return [list(map(float, row)) for row in model.encode(texts)]


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0.0 or nb == 0.0:
        return 0.0
    return dot / (na * nb)
