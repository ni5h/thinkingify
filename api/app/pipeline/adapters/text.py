"""Text generation adapters.

`claude` reuses the existing forced-tool client (app/services/anthropic_client)
so structured output is schema-guaranteed. `stub` returns schema-shaped
placeholder output with no API key, for a dry run or tests that don't inject
their own fake.
"""
from __future__ import annotations

from app.core.config import settings
from app.services.anthropic_client import send_structured


class ClaudeTextAdapter:
    name = "claude"

    def __init__(self, model: str | None = None) -> None:
        # Optional per-role model (generation vs critique); falls back to the
        # app-wide anthropic_model inside send_structured when unset.
        self._model = model

    async def generate(self, *, system: str, prompt: str, tool: dict) -> dict:
        # send_structured reads settings.anthropic_model; temporarily override
        # only when a role-specific model is configured.
        if self._model:
            original = settings.anthropic_model
            settings.anthropic_model = self._model
            try:
                return await send_structured(
                    system=system, messages=[{"role": "user", "content": prompt}], tool=tool
                )
            finally:
                settings.anthropic_model = original
        return await send_structured(
            system=system, messages=[{"role": "user", "content": prompt}], tool=tool
        )


class StubTextAdapter:
    """Builds a dict from the tool's required properties with placeholder values
    — enough to run the pipeline shape without a key. Not for real content."""

    name = "stub"

    def __init__(self, model: str | None = None) -> None:
        self._model = model

    async def generate(self, *, system: str, prompt: str, tool: dict) -> dict:
        schema = tool.get("input_schema", {})
        return _placeholder(schema)


def _placeholder(schema: dict):
    kind = schema.get("type")
    if kind == "object":
        props = schema.get("properties", {})
        required = schema.get("required", list(props.keys()))
        return {key: _placeholder(props.get(key, {})) for key in required}
    if kind == "array":
        return [_placeholder(schema.get("items", {}))]
    if kind == "integer":
        return 0
    if kind == "number":
        return 0.0
    if kind == "boolean":
        return False
    return "(stub)"
