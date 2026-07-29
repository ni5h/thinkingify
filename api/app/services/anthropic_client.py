import httpx

from app.core.config import settings

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
MAX_REPLY_TOKENS = 1024

# Forced tool-choice structured output — guaranteed-schema, unlike hoping
# a free-text reply happens to contain valid JSON. companion_service reads
# only this tool's `input`, never raw response text, so ladder_level and
# direct_answer_requested are always present and always the right shape.
_SUBMIT_REPLY_TOOL = {
    "name": "submit_reply",
    "description": (
        "Submit your reply to the kid, along with your assessment of this turn. "
        "Always call this tool instead of replying directly."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "reply": {
                "type": "string",
                "description": "Your warm, short, in-character reply to show the kid directly.",
            },
            "ladder_level": {
                "type": "integer",
                "minimum": 1,
                "maximum": 4,
                "description": (
                    "How far up the response ladder this reply sits: 1=open question, "
                    "2=point to their own notes/material, 3=reduce scope, 4=process nudge. "
                    "Use 1 unless the kid is still stuck on the exact same thing as last turn."
                ),
            },
            "direct_answer_requested": {
                "type": "boolean",
                "description": (
                    "True if the kid's message was asking you to just give them the "
                    "answer or write the content for them directly."
                ),
            },
        },
        "required": ["reply", "ladder_level", "direct_answer_requested"],
    },
}


class AnthropicClientError(Exception):
    """Raised for any failure that prevents returning a usable structured reply.

    Deliberately a single exception type — companion_service's fail-soft
    handler doesn't need to distinguish a timeout from a malformed response
    from a non-200 status, only that no usable reply came back.
    """


async def send_structured(system: str, messages: list[dict[str, str]]) -> dict:
    if not settings.anthropic_api_key:
        raise AnthropicClientError("Anthropic API key is not configured.")

    payload = {
        "model": settings.anthropic_model,
        "max_tokens": MAX_REPLY_TOKENS,
        "system": system,
        "messages": messages,
        "tools": [_SUBMIT_REPLY_TOOL],
        "tool_choice": {"type": "tool", "name": "submit_reply"},
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
        if block.get("type") == "tool_use" and block.get("name") == "submit_reply":
            tool_input = block.get("input")
            if not isinstance(tool_input, dict) or "reply" not in tool_input:
                raise AnthropicClientError("Anthropic tool response missing expected fields.")
            return tool_input

    raise AnthropicClientError("Anthropic response did not include the expected tool call.")
