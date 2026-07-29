import httpx

from app.core.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MAX_REPLY_TOKENS = 1024


class AnthropicClientError(Exception):
    """Raised for any failure that prevents returning a usable structured reply.

    Deliberately a single exception type — callers' fail-soft handlers don't
    need to distinguish a timeout from a malformed response from a non-200
    status, only that no usable reply came back.
    """


async def send_structured(*, system: str, messages: list[dict[str, str]], tool: dict) -> dict:
    """Forced tool-choice structured output — guaranteed-schema, unlike
    hoping a free-text reply happens to contain valid JSON. `tool` is a full
    Anthropic tool definition (name/description/input_schema); the caller
    owns its schema and is responsible for validating the fields it cares
    about on the returned dict — this function only guarantees a dict came
    back from the named tool, not that any particular key is present.
    """
    if not settings.anthropic_api_key:
        raise AnthropicClientError("Anthropic API key is not configured.")

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": MAX_REPLY_TOKENS,
        "system": system,
        "messages": messages,
        "tools": [tool],
        "tool_choice": {"type": "tool", "name": tool["name"]},
    }
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": ANTHROPIC_VERSION,
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=settings.anthropic_timeout_seconds) as client:
            response = await client.post(ANTHROPIC_API_URL, json=payload, headers=headers)
    except httpx.HTTPError as exc:
        raise AnthropicClientError(f"Request to Anthropic failed: {exc}") from exc

    if response.status_code != 200:
        raise AnthropicClientError(f"Anthropic returned {response.status_code}: {response.text[:500]}")

    data = response.json()
    for block in data.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == tool["name"]:
            tool_input = block.get("input")
            if not isinstance(tool_input, dict):
                raise AnthropicClientError("Anthropic tool response was not an object.")
            return tool_input

    raise AnthropicClientError("Anthropic response did not include the expected tool call.")
