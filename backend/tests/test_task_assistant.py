import pytest

from app.core.exceptions import AIProviderError, InvalidAIResponseError
from app.services.task_assistant import TaskAssistant
from tests.support.ai_recommendation_payloads import VALID_RECOMMENDATION
from tests.support.fake_ai_provider import FakeAIProvider


def test_valid_recommendation_is_returned():
    provider = FakeAIProvider(raw_payload=VALID_RECOMMENDATION)
    result = TaskAssistant(provider).assist("some task-specific prompt")

    assert result.summary == "Use a unique database constraint."
    assert result.confidence == "MEDIUM"
    assert result.files_to_change == ["url_service.py"]


def test_provider_failure_is_not_swallowed():
    provider = FakeAIProvider(error=AIProviderError("simulated timeout"))
    with pytest.raises(AIProviderError):
        TaskAssistant(provider).assist("prompt")


def test_malformed_response_missing_required_field_is_rejected():
    provider = FakeAIProvider(raw_payload={"summary": "incomplete"})
    with pytest.raises(InvalidAIResponseError):
        TaskAssistant(provider).assist("prompt")


def test_response_with_invalid_confidence_value_is_rejected():
    payload = {**VALID_RECOMMENDATION, "confidence": "VERY_SURE"}
    provider = FakeAIProvider(raw_payload=payload)
    with pytest.raises(InvalidAIResponseError):
        TaskAssistant(provider).assist("prompt")


def test_provider_exposes_provider_and_model_identity():
    provider = FakeAIProvider(
        raw_payload=VALID_RECOMMENDATION, provider_name="fake", model_name="fake-model-v1"
    )
    assert provider.provider_name == "fake"
    assert provider.model_name == "fake-model-v1"
