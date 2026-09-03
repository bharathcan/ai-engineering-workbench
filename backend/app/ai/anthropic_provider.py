import json

from anthropic import Anthropic, APIConnectionError, APIError, APIStatusError, APITimeoutError
from pydantic import ValidationError

from app.ai.base import AIProvider, T
from app.core.exceptions import AIProviderError, InvalidAIResponseError

_TOOL_NAME = "emit_result"


class AnthropicProvider(AIProvider):
    """AIProvider backed by the Anthropic Messages API.

    Structured output is obtained via a forced tool call: the response
    schema is passed as the tool's input_schema, and the model is required
    to call that tool, so its output arrives as schema-shaped JSON rather
    than free-form text that would need separate extraction.
    """

    def __init__(self, api_key: str, model: str):
        self._client = Anthropic(api_key=api_key)
        self._model = model

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model

    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        try:
            response = self._client.messages.create(
                model=self._model,
                max_tokens=16384,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                tools=[
                    {
                        "name": _TOOL_NAME,
                        "description": f"Emit the result as {response_model.__name__}.",
                        "input_schema": response_model.model_json_schema(),
                    }
                ],
                tool_choice={"type": "tool", "name": _TOOL_NAME},
            )
        except (APIConnectionError, APITimeoutError, APIStatusError, APIError) as exc:
            raise AIProviderError(f"Anthropic API call failed: {exc}") from exc

        if response.stop_reason == "max_tokens":
            raise InvalidAIResponseError(
                "Anthropic response was truncated by the max_tokens limit before the "
                "tool call could complete — the response is not valid JSON to parse."
            )

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise InvalidAIResponseError("Anthropic response did not include a tool_use block.")

        try:
            return response_model.model_validate(tool_use_block.input)
        except ValidationError as first_exc:
            # Observed live, once: for a large, text-heavy schema (a design
            # task's artifacts, full of multi-line escaped code/markdown),
            # the model emitted a field's value as a JSON-encoded *string*
            # instead of the native list/object the schema expects — e.g.
            # {"artifacts": "{\"artifacts\": [...]}"} instead of
            # {"artifacts": [...]}. If exactly one top-level field is a
            # string that itself parses as JSON, retry validation against
            # that unwrapped value before giving up.
            unwrapped = _unwrap_stringified_field(tool_use_block.input)
            if unwrapped is not None:
                try:
                    return response_model.model_validate(unwrapped)
                except ValidationError:
                    pass
            raise InvalidAIResponseError(
                f"AI output failed schema validation: {first_exc}",
                raw_output=json.dumps(tool_use_block.input),
            ) from first_exc


def _unwrap_stringified_field(raw_input: object) -> dict | None:
    """If raw_input is a dict with a field whose value is a JSON string
    that itself decodes to a dict containing that same field, unwrap it —
    return a corrected copy with the string replaced by its parsed value.
    Returns None if raw_input doesn't match this specific shape."""
    if not isinstance(raw_input, dict):
        return None
    for key, value in raw_input.items():
        if not isinstance(value, str):
            continue
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            continue
        if isinstance(parsed, dict) and key in parsed:
            return {**raw_input, key: parsed[key]}
        if isinstance(parsed, list):
            return {**raw_input, key: parsed}
    return None
