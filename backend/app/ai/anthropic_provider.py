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
                max_tokens=4096,
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

        tool_use_block = next(
            (block for block in response.content if block.type == "tool_use"), None
        )
        if tool_use_block is None:
            raise InvalidAIResponseError("Anthropic response did not include a tool_use block.")

        try:
            return response_model.model_validate(tool_use_block.input)
        except ValidationError as exc:
            raise InvalidAIResponseError(
                f"AI output failed schema validation: {exc}",
                raw_output=json.dumps(tool_use_block.input),
            ) from exc
