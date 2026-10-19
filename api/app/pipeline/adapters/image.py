"""Image adapters.

Only the stub exists for now: the pipeline always produces the per-card visual
*brief* (the house-style description a real generator or illustrator works
from), and the stub returns that brief as a placeholder. A real provider
(OpenAI / Imagen / Stability) is wired later behind this same interface without
touching the generators.
"""
from __future__ import annotations

from app.pipeline.adapters.base import ImageResult


class StubImageAdapter:
    name = "stub"

    def generate(self, brief: str) -> ImageResult:
        return ImageResult(brief=brief, url=None, placeholder=True)
