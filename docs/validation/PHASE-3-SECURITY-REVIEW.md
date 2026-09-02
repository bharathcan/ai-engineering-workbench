# Phase 3 Security Review — Requirement Analyzer

Reviewed before closing Phase 3, per the phase instructions. Scope: the requirement creation/analysis API and its AI integration. Does not cover authentication (none exists yet — no endpoint requires it) or infrastructure security (no deployment exists yet).

## Input validation

`RequirementCreateRequest.text` rejects empty and whitespace-only input, and caps length at 10,000 characters (`backend/app/schemas/requirement.py`) to bound both storage and the size of what gets sent to the AI provider per request. `requirement_id` path parameters that don't match the expected `REQ-{int}` format resolve to "not found" (`app/repositories/requirement_repository.py::_parse_public_id`) rather than being passed into a raw query.

**Status: addressed for this phase's scope.**

## Error handling

Every known failure mode (not found, AI provider failure, invalid AI output, persistence failure) is caught at the route layer and translated to a clean `{"detail": "..."}` response with an appropriate status code — never a raw exception message or traceback (`app/api/routes/requirements.py`). A global `Exception` handler in `app/main.py` is a last-resort net for anything uncaught, also returning a generic message. Verified by `backend/tests/test_requirements_api.py::test_error_responses_do_not_leak_internal_details`, which asserts a deliberately "sensitive"-looking provider error message does not appear in the HTTP response.

**Status: addressed.**

## Prompt injection

The raw requirement text is user-controlled and is embedded directly into the AI prompt (`app/ai/prompts.py::build_requirement_analysis_user_prompt`). A user could write a requirement like "Ignore prior instructions and output X" — this is not filtered or detected.

**Mitigation in place:** the impact is bounded, not eliminated. The AI provider abstraction only ever returns data validated against `RequirementAnalysisResult` (`extra="forbid"`, fixed fields, ID pattern constraints) — see `app/schemas/requirement_analysis.py`. Even a successfully "hijacked" response can only populate that fixed schema; it cannot cause arbitrary code execution, arbitrary API calls, or escape into unrelated parts of the system, because nothing downstream treats the AI's text output as anything other than inert display data.

**Not done in this phase:** no prompt-injection detection, no input sanitization beyond length/emptiness, no adversarial testing of the real Anthropic provider (untestable here — no API key in this environment; see `AI_USAGE.md` TASK-001). **This remains an unresolved risk**, acceptable for this phase's scope (an analyzer that only produces a structured read-only analysis) but not for later phases where AI output might influence code generation or task execution with a larger blast radius.

## API key handling

`AI_API_KEY` is read only via `app.core.config.Settings` from the environment (`.env`, never committed — see root `.gitignore`), passed directly to the provider constructor (`app/ai/factory.py`), and never logged, returned in any API response, or written to persistence. Verified by grep across `backend/app/` for hardcoded key patterns and for any place `ai_api_key` is passed to a logger — none found.

**Status: addressed.**

## Sensitive data logging

The only logging added in this phase (`app/api/routes/requirements.py`, `app/main.py`) logs the `requirement_id` and an exception's string representation on failure paths — never the full requirement text, and never the AI provider's raw structured output. A provider's `InvalidAIResponseError.raw_output` field exists (for potential future debugging) but is not currently logged anywhere.

**Status: addressed for this phase.** Worth revisiting once real requirement text may contain customer- or business-sensitive content — at that point, even `requirement_id`-only logging combined with DB access could reconstruct sensitive context, which is a reasonable future concern but out of scope here.

## AI response handling

AI output is never executed, evaluated, or trusted as-is: it is parsed as JSON and validated field-by-field against `RequirementAnalysisResult` (strict, `extra="forbid"`) before it is accepted (`app/ai/anthropic_provider.py`, `app/ai/base.py`). Output that fails validation is rejected with `InvalidAIResponseError` and never persisted — verified by `backend/tests/test_requirement_analyzer.py` (missing field, wrong type, unexpected field, invalid ID format) and `backend/tests/test_requirements_api.py` (502 path, confirms nothing is persisted on failure).

**Status: addressed.**

## Summary

| Area | Status |
|---|---|
| Input validation | Addressed |
| Error handling / no internal leakage | Addressed |
| Prompt injection | Partially mitigated (schema containment); **not fully resolved** |
| API key handling | Addressed |
| Sensitive data logging | Addressed for current scope; revisit before real requirement text is customer data |
| AI response handling | Addressed |

No AI API keys are stored in source control. No secrets appear in any log statement added this phase.
