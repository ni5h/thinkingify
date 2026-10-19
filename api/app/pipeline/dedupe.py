"""Dedupe generated items against each other and the private reference set.

Embeds locally (the reference text never leaves the machine), records each
item's nearest-neighbour cosine as its dedupe_score, and drops items at or above
the threshold. Greedy: the first of a near-duplicate pair is kept, later ones
dropped.
"""
from __future__ import annotations

from app.pipeline.adapters.base import EmbeddingAdapter
from app.pipeline.adapters.embeddings import cosine
from app.pipeline.types import GeneratedItem


def dedupe(
    items: list[GeneratedItem],
    *,
    reference_texts: list[str],
    adapter: EmbeddingAdapter,
    threshold: float,
) -> tuple[list[GeneratedItem], list[GeneratedItem]]:
    if not items:
        return [], []

    item_vecs = adapter.embed([it.body for it in items])
    ref_vecs = adapter.embed(reference_texts) if reference_texts else []

    kept: list[GeneratedItem] = []
    dropped: list[GeneratedItem] = []
    kept_vecs: list[list[float]] = []

    for it, vec in zip(items, item_vecs):
        best = 0.0
        for kv in kept_vecs:
            best = max(best, cosine(vec, kv))
        for rv in ref_vecs:
            best = max(best, cosine(vec, rv))
        it.dedupe_score = best
        if best >= threshold:
            dropped.append(it)
        else:
            kept.append(it)
            kept_vecs.append(vec)

    return kept, dropped
