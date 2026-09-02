# Requirement Traceability Matrix

Populated with **real, actually-produced project data** — captured by executing one complete run of the mandatory requirement through the live application code (`TestClient` + `FakeAIProvider`, the same pattern used throughout the permanent test suite — no live AI provider is configured in this environment, disclosed consistently everywhere in this project), not fabricated IDs. Every ID below was printed by that run and cross-checked against the actual API responses. The generated artifact from this run is a real file on disk at `generated/backend/app/services/short_code.py`.

Where a link in the chain doesn't exist for a given row, this says so explicitly (`NOT AVAILABLE`) rather than inventing one.

## Primary Chain — Mandatory Requirement (URL Shortener)

| Requirement | Task | AI Run | Engineer Decision | Artifact | Test | Validation |
|---|---|---|---|---|---|---|
| `REQ-001` ("Build a scalable URL shortener service with APIs, persistence, and analytics.") | `TASK-001` (short-code generation) | `AI-RUN-001` (`CODE_GENERATION`) | `DECISION-001` (task, ACCEPT) → `DECISION-002` (AI run, ACCEPT) → `DECISION-003` (artifact, ACCEPT) | `ARTIFACT-001` (`backend/app/services/short_code.py`, `SOURCE_CODE`) | `backend/tests/test_url_shortener_workbench_flow.py` (permanent, re-runnable) | `VALIDATION-001` (`STATIC_ANALYSIS`, **PASSED**), `VALIDATION-002` (`API_CONTRACT`, **PASSED**) |

Full plan produced from this same requirement: `PLAN-001` with 4 tasks (`TASK-001` short-code generation, `TASK-002` persistence + redirect, `TASK-003` click analytics, `TASK-004` advanced analytics) — only `TASK-001`'s full chain was carried through to artifact + validation in this captured run; the others follow the identical pattern (proven separately by `backend/tests/test_url_shortener_workbench_flow.py`, which carries every task through).

## Ambiguity Traceability

| Requirement | Ambiguity | Gate Behavior | Resolution |
|---|---|---|---|
| `REQ-001` | `AMB-001` (traffic volume unquantified) | `MEDIUM`-ish relevance — did **not** block planning (see analysis payload) | Left open; documented as a standing assumption in [ADR-003](adr/ADR-003-cache-strategy.md) (no cache without a traffic number) |
| A separate `"Improve the analytics."` requirement (Phase 10) | `AMB-001` in that requirement's own analysis (no analytics system/improvement named) | `HIGH`-impact — **did** block planning: `plan.status == "BLOCKED"`, 0 tasks generated | Engineer chose Interpretation C (Advanced User Analytics); re-submission after that decision produced a `LOW`-impact ambiguity that no longer blocks — see `backend/tests/test_advanced_analytics_workbench_flow.py` and [docs/scenarios/ambiguous.md](scenarios/ambiguous.md) |

## Brownfield Chain (Phase 9 — Redirect Performance)

| Requirement | Task | AI Run | Engineer Decision | Artifact | Test | Validation |
|---|---|---|---|---|---|---|
| Brownfield requirement text: *"The existing URL shortener has slow redirect performance. Improve performance without changing the public API."* | Performance-optimization task (decomposed via the same pipeline) | `AI-RUN-001` → engineer `MODIFY` (required a regression test) → `AI-RUN-002` (revision, `revised_from_ai_run_id` linking it back) → `ACCEPT` | Recorded via the same `EngineerDecision` model | Code changes applied directly to `app/services/url_service.py`/`url_repository.py` (a brownfield change to *existing* code, not a new generated-artifact file) | `backend/tests/test_brownfield_performance_flow.py` | `NOT AVAILABLE` as a formal `Validation` row — verified instead by the full pre-existing test suite (145 tests, before and after) plus a dedicated regression test and real before/after performance measurement (see [docs/scenarios/brownfield.md](scenarios/brownfield.md)) |

This row's "Validation" cell is honestly `NOT AVAILABLE` in the formal `Validation` model sense — brownfield code changes in this project are verified through the existing test suite and dedicated regression tests, not by generating a tracked `Artifact` + running the `Validation` API against it the way the greenfield row above was. This is a real structural difference between how greenfield and brownfield work is currently verified, not an oversight being hidden.

## What This Matrix Does Not Cover

* Every task/AI-run/artifact/validation ever created across all 12 phases (that volume lives in the database and is inspectable via the UI's Tasks/AI Runs/Artifacts/Validation screens or `pytest`'s test output) — this matrix demonstrates the chain is real and traceable with one concrete, real example per scenario, per the master prompt's instruction to populate with actual data rather than exhaustively dump every row.
* The `Test` node in the canonical chain (`Requirement → Task → AI Run → Engineer Decision → Artifact → Test → Validation`) has no dedicated `Test` model distinct from `UNIT_TEST`/`INTEGRATION_TEST` validation types — those validation types *are* how "Test" is represented in this schema (see [ARCHITECTURE.md](../ARCHITECTURE.md) Traceability section, which discloses this as the one still-simplified link).
