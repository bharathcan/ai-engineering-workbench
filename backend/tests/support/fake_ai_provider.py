import json

from pydantic import BaseModel, ValidationError

from app.ai.base import AIProvider, T
from app.core.exceptions import InvalidAIResponseError


class FakeAIProvider(AIProvider):
    """Test double for AIProvider. Never calls a real AI API — tests control
    exactly what "the AI" returns, including failure modes.

    Exactly one of `response`, `raw_payload`, or `error` should be set:
    - `response`: a ready-made, already-valid model instance to return.
    - `raw_payload`: a dict validated against response_model the same way a
      real provider's tool-call output would be — use this to simulate
      malformed/missing/unexpected-field AI output.
    - `error`: an exception instance to raise, simulating a provider-side
      failure (timeout, network, rate limit).
    """

    def __init__(
        self,
        *,
        response: BaseModel | None = None,
        raw_payload: dict | None = None,
        error: Exception | None = None,
        provider_name: str = "fake",
        model_name: str = "fake-model",
    ):
        self._response = response
        self._raw_payload = raw_payload
        self._error = error
        self._provider_name = provider_name
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return self._provider_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        if self._error is not None:
            raise self._error

        if self._raw_payload is not None:
            try:
                return response_model.model_validate(self._raw_payload)
            except ValidationError as exc:
                raise InvalidAIResponseError(
                    f"AI output failed schema validation: {exc}",
                    raw_output=json.dumps(self._raw_payload),
                ) from exc

        if self._response is not None:
            return self._response

        raise AssertionError("FakeAIProvider was not configured with a response for this test.")
