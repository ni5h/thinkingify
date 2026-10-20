"""Image adapters.

- `stub`: produces the per-card visual *brief* as a placeholder (no real image).
- `svg`: a free "first pass" — Claude draws an original, flat cartoon as inline
  SVG from the card's brief. Simple and original only (a cow, a leaf, a tooth),
  never a recognizable or copyrighted character. A richer raster provider can
  replace this behind the same interface later.
"""
from __future__ import annotations

import re

from app.pipeline.adapters.base import ImageResult
from app.services.anthropic_client import AnthropicClientError, send_structured

_SCRIPT = re.compile(r"<script\b.*?</script>", re.I | re.S)


class StubImageAdapter:
    name = "stub"

    async def generate(self, brief: str) -> ImageResult:
        return ImageResult(brief=brief, url=None, svg=None, placeholder=True)


_SVG_SYSTEM = (
    "You draw a single, simple, flat cartoon illustration as inline SVG for a "
    "nine-year-old's lesson card. Rules: ONE clear subject; friendly, rounded, "
    "flat style; ORIGINAL art only — never a known, branded or copyrighted "
    "character; little or no text; an age-appropriate, non-scary depiction. "
    "Use a square viewBox (0 0 240 240), simple shapes and paths, and colours "
    "from this palette where they fit: teal #14746F, ink #16213B, amber #F5C26B, "
    "soft #E3E8EF, white #FFFFFF. Return one self-contained <svg>…</svg> with the "
    "viewBox set, no <script>, no external images, no fonts."
)

_SVG_TOOL = {
    "name": "illustration",
    "description": "Return one inline SVG illustration.",
    "input_schema": {
        "type": "object",
        "required": ["svg"],
        "properties": {"svg": {"type": "string", "description": "A complete <svg>…</svg> element."}},
    },
}


class ClaudeSvgImageAdapter:
    name = "svg"

    async def generate(self, brief: str) -> ImageResult:
        try:
            out = await send_structured(
                system=_SVG_SYSTEM,
                messages=[{"role": "user", "content": f"Draw: {brief}"}],
                tool=_SVG_TOOL,
                max_tokens=3000,
                timeout=120.0,
            )
        except AnthropicClientError:
            # Never fail generation on a bad illustration — fall back to a brief.
            return ImageResult(brief=brief, url=None, svg=None, placeholder=True)
        svg = str(out.get("svg", "")).strip()
        svg = _SCRIPT.sub("", svg)  # defensive: strip any script
        if "<svg" not in svg:
            return ImageResult(brief=brief, url=None, svg=None, placeholder=True)
        return ImageResult(brief=brief, url=None, svg=svg, placeholder=False)
