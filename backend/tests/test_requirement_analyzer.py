import pytest

from app.core.exceptions import AIProviderError, InvalidAIResponseError
from app.services.requirement_analyzer import RequirementAnalyzer
from tests.support.analysis_payloads import (
    AMBIGUOUS_ANALYTICS_ANALYSIS,
    MINIMAL_API_ANALYSIS,
    VALID_URL_SHORTENER_ANALYSIS,
)
from tests.support.fake_ai_provider import FakeAIProvider


def test_valid_requirement_produces_structured_analysis():
    provider = FakeAIProvider(raw_payload=VALID_URL_SHORTENER_ANALYSIS)
    analyzer = RequirementAnalyzer(provider)

    result = analyzer.analyze(
        "Build a scalable URL shortener service with APIs, persistence, and analytics."
    )

    assert result.summary
    assert len(result.functional_requirements) == 3
    assert result.functional_requirements[0].id == "FR-001"
    assert len(result.ambiguities) == 1
    assert result.ambiguities[0].impact == "MEDIUM"


def test_ambiguous_requirement_is_flagged_as_ambiguity_not_assumption():
    provider = FakeAIProvider(raw_payload=AMBIGUOUS_ANALYTICS_ANALYSIS)
    analyzer = RequirementAnalyzer(provider)

    result = analyzer.analyze("Improve the analytics.")

    assert len(result.ambiguities) >= 1
    assert result.ambiguities[0].impact == "HIGH"
    # The ambiguity must not have been silently resolved into an assumption.
    assert len(result.assumptions) == 0


def test_minimal_requirement_does_not_produce_inflated_analysis():
    provider = FakeAIProvider(raw_payload=MINIMAL_API_ANALYSIS)
    analyzer = RequirementAnalyzer(provider)

    result = analyzer.analyze("Build an API.")

    assert len(result.functional_requirements) == 1
    assert len(result.non_functional_requirements) == 0
    assert len(result.ambiguities) >= 1


def test_provider_failure_is_not_swallowed():
    provider = FakeAIProvider(error=AIProviderError("simulated timeout"))
    analyzer = RequirementAnalyzer(provider)

    with pytest.raises(AIProviderError):
        analyzer.analyze("Build a scalable URL shortener.")


def test_malformed_ai_response_missing_required_field_is_rejected():
    payload = {**VALID_URL_SHORTENER_ANALYSIS, "summary": None}  # required field, wrong type
    provider = FakeAIProvider(raw_payload=payload)
    analyzer = RequirementAnalyzer(provider)

    with pytest.raises(InvalidAIResponseError):
        analyzer.analyze("Build a scalable URL shortener.")


def test_ai_response_missing_field_entirely_is_rejected():
    payload = dict(VALID_URL_SHORTENER_ANALYSIS)
    del payload["ambiguities"]
    provider = FakeAIProvider(raw_payload=payload)
    analyzer = RequirementAnalyzer(provider)

    with pytest.raises(InvalidAIResponseError):
        analyzer.analyze("Build a scalable URL shortener.")


def test_ai_response_with_unexpected_field_is_rejected():
    payload = {**VALID_URL_SHORTENER_ANALYSIS, "unexpected_field": "should not be here"}
    provider = FakeAIProvider(raw_payload=payload)
    analyzer = RequirementAnalyzer(provider)

    with pytest.raises(InvalidAIResponseError):
        analyzer.analyze("Build a scalable URL shortener.")


def test_ai_response_with_invalid_id_format_is_rejected():
    payload = {
        **VALID_URL_SHORTENER_ANALYSIS,
        "functional_requirements": [{"id": "1", "description": "Not a valid ID format."}],
    }
    provider = FakeAIProvider(raw_payload=payload)
    analyzer = RequirementAnalyzer(provider)

    with pytest.raises(InvalidAIResponseError):
        analyzer.analyze("Build a scalable URL shortener.")
