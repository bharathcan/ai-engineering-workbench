# Phase 4 Security Review — Task Decomposition

Reviewed before closing Phase 4. Scope: the task-decomposition API, its AI integration, and the review-decision endpoint. Builds on [PHASE-3-SECURITY-REVIEW.md](PHASE-3-SECURITY-REVIEW.md), which still applies to everything it covered (requirement intake, API key handling, error handling patterns) — this document covers what's new in Phase 4.

## Task input validation

There is no direct "create a task" endpoint — tasks only ever come from `TaskDecomposer` output, which is schema-validated (`extra="forbid"`, `Literal` types for `type`/`ai_assistance_type`, ID patterns) before it can become a task at all (`app/schemas/task_decomposition.py`). The one endpoint that takes direct user input in this phase, `POST /api/v1/tasks/{task_id}/decision`, validates `decision` against a fixed `Literal["ACCEPT","MODIFY","REJECT"]` and requires non-empty `rationale`/`changes` where the decision demands them (`app/schemas/engineering_plan.py::TaskDecisionRequest`).

**Status: addressed.**

## Unexpected AI output

Beyond Phase 3's schema validation, task decomposition adds a referential-integrity layer that Pydantic field types alone cannot express: duplicate task ids, self-dependencies, dependencies on unknown task ids, circular dependencies (DFS cycle detection), `requirement_refs` pointing to an id not present in the actual analysis, and a task's `sequence` not coming after its dependencies' — all implemented in `app/services/task_decomposer.py::_validate_task_plan` and raising the same `InvalidAIResponseError` → `502` path as a schema failure. None of this is optimistic parsing: any single violation rejects the entire plan, and nothing is persisted on rejection (verified by `backend/tests/test_tasks_api.py::test_malformed_plan_returns_502_and_does_not_persist`).

**Status: addressed.**

## Injection content flowing from requirements

The requirement's raw text and its (already-reviewed) analysis are both embedded in the task-decomposition prompt (`app/ai/prompts.py::build_task_decomposition_user_prompt`). This is the same category of risk documented in Phase 3 (prompt injection via user-controlled text) and the same mitigation applies: AI output can only ever populate the fixed `TaskDecompositionResult` schema plus pass the referential-integrity checks above — a successfully "hijacked" response still cannot produce anything but a structured, reviewable task list. It specifically **cannot** produce or trigger code execution: the prompt explicitly instructs "do not generate implementation code" (`TASK_DECOMPOSITION_SYSTEM_PROMPT`), and even if a response violated that instruction, `description`/`title`/`acceptance_criteria` are plain string fields — the API never executes, evaluates, or interprets their contents as anything but display text.

**Not done in this phase**, same as Phase 3: no prompt-injection detection or adversarial testing against the real Anthropic provider (no API key in this environment). **This remains an unresolved risk**, tracked jointly with the Phase 3 finding.

## Dependency validation

Covered above under "Unexpected AI output" — this is the phase's largest new validation surface, and it is exercised by 8 dedicated unit tests in `backend/tests/test_task_decomposer.py` (empty list, self-dependency, missing reference, circular dependency, unknown requirement ref, sequence inconsistency, unsupported type, duplicate id) plus the end-to-end `502` path in the API tests.

**Status: addressed.**

## Authorization assumptions

**Unresolved, same as Phase 3 (not newly introduced, but newly relevant):** no endpoint in this codebase requires authentication. `POST /api/v1/tasks/{task_id}/decision` — recording an ACCEPT/MODIFY/REJECT decision — is exactly the kind of action that would need to be attributable to a specific engineer in a multi-user deployment, and right now it is not: `EngineerDecision` has no `decided_by` field, and anyone who can reach the API can decide any task. This is acceptable for a single-engineer local development phase but is flagged explicitly as a gap, not silently deferred — no authentication or authorization exists anywhere in this system yet.

## Error handling

Every new failure mode (requirement not analyzed — `409`, plan/task not found — `404`, AI failure — `503`, invalid AI output — `502`, persistence failure — `500`, decision validation — `422`) is caught at the route layer and mapped to a clean `{"detail": "..."}` response, following the exact pattern established in Phase 3 (`app/api/routes/tasks.py`). The existing global exception handler in `app/main.py` remains the last-resort safety net.

**Status: addressed.**

## Sensitive content logging

Logging added this phase (`app/api/routes/tasks.py`) follows the Phase 3 pattern: `requirement_id`/`task_id` and an exception's string form only — never the requirement's full text, the full analysis, or the full generated task plan. An engineer's `rationale`/`changes` text on a decision is persisted (by design — it's the audit record) but not separately logged.

**Status: addressed for this phase**, same caveat as Phase 3: once requirement text is real business content, even id-only logging plus DB access could reconstruct sensitive context — a future concern, not resolved here.

## Summary

| Area | Status |
|---|---|
| Task input validation | Addressed |
| Unexpected AI output | Addressed |
| Prompt injection via requirement content | Partially mitigated (schema + referential-integrity containment); **not fully resolved** |
| Dependency validation | Addressed |
| Authorization | **Unresolved** — no authentication/authorization exists anywhere in this system |
| Error handling | Addressed |
| Sensitive content logging | Addressed for current scope |

No AI API keys are stored in source control. No secrets appear in any log statement added this phase.
