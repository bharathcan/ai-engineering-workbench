from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class AIProvider(ABC):
    """Provider-agnostic interface for requesting schema-validated AI output.

    Callers never see provider-specific request/response shapes — they hand
    over a system prompt, a user prompt, and the Pydantic model the response
    must conform to, and get back a validated instance of that model or a
    typed error (app.core.exceptions.AIProviderError /
    InvalidAIResponseError). No caller in this codebase should import a
    specific provider implementation directly.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Identifies which provider actually ran, for AIRun persistence
        (app.models.engineering_plan.AIRun) — not for branching logic."""
        raise NotImplementedError

    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def complete_structured(
        self, *, system_prompt: str, user_prompt: str, response_model: type[T]
    ) -> T:
        """Request output from the model, validated against response_model.

        Raises:
            app.core.exceptions.AIProviderError: the provider call itself
                failed (network, timeout, auth, rate limit).
            app.core.exceptions.InvalidAIResponseError: the provider
                responded, but its output did not validate against
                response_model.
        """
        raise NotImplementedError
