"""Unit tests for AnthropicProvider, mocking the Anthropic client so no
real network call or API cost is incurred. Exercises the exact failure
modes discovered by running the live URL shortener requirement through
the real API (see AI_USAGE.md): a truncated max_tokens response and a
schema-mismatched tool call, plus the success and transport-error paths."""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from anthropic import APIConnectionError
from pydantic import BaseModel

from app.ai.anthropic_provider import AnthropicProvider
from app.core.exceptions import AIProviderError, InvalidAIResponseError


class _Result(BaseModel):
    value: str


class _ListResult(BaseModel):
    artifacts: list[str]


def _tool_use_response(input_payload: dict, stop_reason: str = "tool_use"):
    block = SimpleNamespace(type="tool_use", input=input_payload)
    return SimpleNamespace(content=[block], stop_reason=stop_reason)


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_returns_validated_model_on_success(mock_anthropic_cls):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _tool_use_response({"value": "ok"})
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    result = provider.complete_structured(
        system_prompt="sys", user_prompt="user", response_model=_Result
    )

    assert result == _Result(value="ok")


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_requests_a_generous_token_budget(mock_anthropic_cls):
    """Regression test for two real bugs this fix addresses, both live
    against the URL shortener requirement: task decomposition truncated at
    the original max_tokens=4096, and artifact generation (which must emit
    full file content for every proposed file in one structured call) then
    truncated again at 8192. Pins the budget so it can't silently regress."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _tool_use_response({"value": "ok"})
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    provider.complete_structured(system_prompt="sys", user_prompt="user", response_model=_Result)

    _, kwargs = mock_client.messages.create.call_args
    assert kwargs["max_tokens"] >= 16384


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_raises_on_max_tokens_truncation(mock_anthropic_cls):
    """The exact failure observed live: Claude's structured output ran out
    of token budget mid-generation, so the tool call arrived incomplete —
    e.g. missing the required `tasks` field entirely. stop_reason ==
    "max_tokens" is Anthropic's own signal for this; it must be checked
    before attempting to validate whatever partial input did arrive."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _tool_use_response(
        {"value": "incomple"}, stop_reason="max_tokens"
    )
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    with pytest.raises(InvalidAIResponseError, match="truncated"):
        provider.complete_structured(
            system_prompt="sys", user_prompt="user", response_model=_Result
        )


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_raises_on_schema_mismatch(mock_anthropic_cls):
    """The other real failure observed live: a syntactically complete tool
    call whose content didn't match the schema (e.g. an id field with an
    unexpected suffix). Must be rejected, not coerced or accepted as-is,
    and the raw output must be preserved on the exception for diagnosis."""
    mock_client = MagicMock()
    mock_client.messages.create.return_value = _tool_use_response({"wrong_field": "oops"})
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    with pytest.raises(InvalidAIResponseError) as exc_info:
        provider.complete_structured(
            system_prompt="sys", user_prompt="user", response_model=_Result
        )

    assert exc_info.value.raw_output is not None
    assert "wrong_field" in exc_info.value.raw_output


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_unwraps_a_stringified_json_field(mock_anthropic_cls):
    """The other real failure observed live, for a large text-heavy
    artifact-generation response: the model emitted its own field's value
    as a JSON-encoded string instead of a native list — e.g.
    {"artifacts": "{\\"artifacts\\": [...]}"} instead of the schema's
    expected {"artifacts": [...]}. Rather than reject a response that
    actually contains the right data one encoding layer too deep, unwrap
    it and validate the recovered value."""
    mock_client = MagicMock()
    inner_json = json.dumps({"artifacts": ["a.py", "b.py"]})
    mock_client.messages.create.return_value = _tool_use_response({"artifacts": inner_json})
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    result = provider.complete_structured(
        system_prompt="sys", user_prompt="user", response_model=_ListResult
    )

    assert result == _ListResult(artifacts=["a.py", "b.py"])


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_raises_when_no_tool_use_block_present(mock_anthropic_cls):
    mock_client = MagicMock()
    text_block = SimpleNamespace(type="text", text="I decided not to call the tool.")
    mock_client.messages.create.return_value = SimpleNamespace(
        content=[text_block], stop_reason="end_turn"
    )
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    with pytest.raises(InvalidAIResponseError, match="tool_use"):
        provider.complete_structured(
            system_prompt="sys", user_prompt="user", response_model=_Result
        )


@patch("app.ai.anthropic_provider.Anthropic")
def test_complete_structured_wraps_transport_failures(mock_anthropic_cls):
    mock_client = MagicMock()
    request = httpx.Request("POST", "https://api.anthropic.com/v1/messages")
    mock_client.messages.create.side_effect = APIConnectionError(request=request)
    mock_anthropic_cls.return_value = mock_client

    provider = AnthropicProvider(api_key="test-key", model="claude-sonnet-5")
    with pytest.raises(AIProviderError):
        provider.complete_structured(
            system_prompt="sys", user_prompt="user", response_model=_Result
        )
