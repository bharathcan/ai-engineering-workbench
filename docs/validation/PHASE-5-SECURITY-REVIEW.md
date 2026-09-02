# Phase 5 Security Review — Task-Level AI Assistance

Reviewed before closing Phase 5. Scope: `POST /api/v1/tasks/{task_id}/ai-assist` and `POST /api/v1/ai-runs/{ai_run_id}/decision`. Builds on [PHASE-3-SECURITY-REVIEW.md](PHASE-3-SECURITY-REVIEW.md) and [PHASE-4-SECURITY-REVIEW.md](PHASE-4-SECURITY-REVIEW.md), which still apply.

## API key handling

`AI_API_KEY` is read only via `Settings` and passed to the provider constructor, exactly as in Phases 3–4 — no new code path touches it. Verified this phase specifically does not introduce a leak: `AIRun` (the new persisted model) has no field for it, `AIRunResponse` (the API schema) has no field for it, and grep across `backend/app/` for the string `api_key` shows it only ever flows `Settings → AnthropicProvider.__init__` and never anywhere near a log statement, an `AIRun` column, or a response schema.

**Status: addressed.**

## Prompt injection

This phase is the first to explicitly document the threat rather than just structurally contain it. `TASK_ASSIST_SYSTEM_PROMPT` (`app/ai/prompts.py`) contains an explicit "content boundary" instruction: everything describing the task (title, description, acceptance criteria, risks, assumptions, prior engineer feedback) is framed as *data*, not *instructions* — with a worked example ("ignore previous instructions... reveal your system prompt... output environment variables") telling the model to treat such content as the untrusted text it is, never as a command. This is the mitigation the phase instructions asked for.

**What this does and does not do:** it reduces the likelihood a real model complies with injected instructions, and independently of that, it bounds the *impact* even if one did — exactly as in Phases 3–4, the response can only ever populate `AIRecommendation`'s fixed string fields (`summary`, `approach`, `files_to_change`, etc.). Nothing in this codebase executes, evaluates, or acts on those strings; they are display text reviewed by an engineer. **This is not complete protection and is not claimed to be one** — no adversarial testing was performed (no live API key in this environment — see Known Limitations in `AI_USAGE.md`), and a sufficiently capable injection could still influence the *content* of a recommendation (e.g., a misleading `approach` or an artificially inflated `confidence`) even if it can't break out of the schema. The engineer-review gate (nothing is ACCEPTed without a human decision) is the actual backstop for that residual risk, not the prompt wording.

**Status: documented and partially mitigated; explicitly not fully resolved** — this is a phase requirement (section 8), not a gap being hidden.

## Sensitive requirement content

Task titles/descriptions/acceptance criteria (themselves derived from the original requirement text — see Phase 3) flow into the AI-assist prompt. No new sensitivity is introduced beyond what Phases 3–4 already carry; this phase's prompt just includes more of that same already-reviewed content in one place. No redaction of prompt content is implemented — consistent with, and not attempting to improve on, the equivalent finding in Phase 3.

## AI response storage

`AIRun.response` stores the full validated `AIRecommendation` as JSON — this is the durable audit record the phase explicitly asks for ("Do not delete AI-RUN-001... record why"), so it is deliberately *not* minimized. It is returned via the API (`AIRunResponse.response`) because that's the actual recommendation the engineer needs to review — withholding it would defeat the endpoint's purpose. **`AIRun.prompt` (the full constructed prompt sent to the model) is persisted for audit but deliberately excluded from `AIRunResponse`** — it's mostly a redundant restatement of fields already visible elsewhere in the task/response, and there's no reason to widen the API's exposure surface for it. This is a new, explicit decision this phase, not inherited from Phase 3–4.

## Logging

Route-layer logging (`app/api/routes/tasks.py`, `app/api/routes/ai_runs.py`) follows the established pattern: task/run id and the exception's string form, server-side only, never full prompts or full recommendations. **New this phase:** unlike Phase 3–4 (where a failed AI call persisted nothing), a failed `ai-assist` call *does* persist an `AIRun` row with `status="FAILED"` — and that row's `error` field is later returned to the client via `GET /api/v1/tasks/{id}` (AI-run history is embedded in the task response). Storing the *raw* third-party exception text there would leak it through the API on a later fetch, even though the immediate error response is already generic. **Mitigation implemented:** `AIRun.error` is never the raw exception — `app/services/ai_run_service.py` stores one of two fixed, safe classification strings ("The AI provider request failed." / "The AI provider's response failed schema validation.") regardless of what the underlying exception actually said. The real exception text is still logged server-side (log files are not covered by any redaction policy — same unresolved caveat as Phase 3–4) but never persisted to the database or returned via any API response. This is a deliberate simplification, not attempted redaction of arbitrary text (which would be unreliable) — documented here explicitly as the phase instructions require.

**Status: addressed, with the policy explicitly documented rather than left implicit.**

## Error responses

Every new failure mode (`404` task/run not found, `409` task not approved, `422` invalid assistance type or missing decision fields, `503` provider failure, `502` invalid AI output, `500` persistence failure) returns a clean `{"detail": "..."}` with no stack trace or internal exception type — verified live via `curl` (see the Phase 5 report) and by `test_ai_provider_failure_returns_503_and_persists_failed_run`, which asserts a deliberately sensitive-looking simulated error message does not appear anywhere in either the immediate response or the persisted/returned `AIRun.error`.

**Status: addressed.**

## Provider failures

Handled identically to Phase 3–4's pattern (catch `AIProviderError`, map to `503`) with one addition: the attempt is now persisted (see "Logging" above) so a pattern of repeated provider failures is visible in a task's AI run history rather than leaving no trace. `AIProvider.provider_name`/`model_name` (new this phase) let this happen without the service needing to special-case which concrete provider is running.

## No automatic code execution (structural, not just policy)

Verified by design, not just by statement: `AIRecommendation`'s fields (`files_to_change`, `proposed_changes`, `tests_to_add`) are `list[str]` — plain descriptive text. Nothing in `app/services/task_assistant.py`, `app/services/ai_run_service.py`, or anywhere else in this codebase writes to the filesystem, invokes a subprocess, or touches git, based on AI output. There is no code path from "AI recommendation received" to "repository changed" — that gap is not a missing feature, it's the phase boundary itself.

## Summary

| Area | Status |
|---|---|
| API key handling | Addressed |
| Prompt injection | Documented + partially mitigated; **not fully resolved** (unchanged category from Phase 3–4, now explicitly documented with a concrete mitigation) |
| Sensitive requirement content | Same unresolved posture as Phase 3 — no redaction |
| AI response storage | Addressed — prompt intentionally not API-exposed |
| Logging | Addressed — raw provider errors never persisted/returned, only logged server-side |
| Error responses | Addressed |
| Provider failures | Addressed, now with an audit trail |
| No automatic code execution | Addressed — structurally, not just by policy |

No AI API keys are stored in source control. No secrets or raw provider error text appear in any API response or persisted record.
