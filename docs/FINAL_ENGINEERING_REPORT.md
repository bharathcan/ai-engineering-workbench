# Final Engineering Report

## Executive Summary

`ai-engineering-workbench` is a working prototype demonstrating AI-assisted software engineering with mandatory human review at every stage. Built across 12 completed, reviewed phases: a FastAPI backend implementing a Requirement Analyzer, Task Decomposer, AI-assistance layer, Artifact Generator, and Validation Engine; a React frontend exposing all of it as a coherent 9-screen UI; the mandatory use case (a URL shortener) built end-to-end through that pipeline, then extended with a brownfield performance fix and an ambiguous-requirement resolution; and a Phase 12 security/performance hardening pass. Every AI-assisted output in this codebase passed through an explicit `ACCEPT`/`MODIFY`/`REJECT` engineer decision before it had any effect — none was auto-applied.

## Engineering Problem

The workbench demonstrates a specific, narrow claim: that AI can be integrated into a real engineering workflow *without* becoming the decision-maker. Concretely, it proves — with real, executed code, not description — that:

* A requirement can be analyzed and its ambiguities surfaced rather than silently resolved.
* An AI recommendation can be generated, reviewed, and explicitly accepted, modified, or rejected — with rejection actually blocking downstream generation, not just being logged.
* Generated code can be sandboxed so AI cannot write outside an approved workspace.
* Validation can run real commands (not simulated results) and honestly distinguish "passed" from "never run."
* A materially ambiguous requirement can be *blocked* rather than guessed at, with the block enforced by code, not policy.

## Architecture

```text
Engineer → UI → Requirement Analyzer → Engineering Planner → AI Assistance
  → Engineer Review → Artifact Generator → Validation Engine → Final Report
```

FastAPI + SQLAlchemy 2.0 + Pydantic v2 backend, SQLite (dev/test) with PostgreSQL as an untested proposed target; React 19 + TypeScript + Vite frontend; Anthropic-backed `AIProvider` abstraction with no live key configured in this environment (`FakeAIProvider` stands in throughout, disclosed everywhere). Full detail in [ARCHITECTURE.md](../ARCHITECTURE.md).

## Requirement Understanding

The Requirement Analyzer produces a structured breakdown (summary, functional/non-functional requirements, ambiguities with an explicit `impact` level, assumptions, constraints, success criteria, engineering concerns) from raw requirement text, via a schema-validated AI call. Ambiguity is a first-class field, not something inferred — see `backend/app/schemas/requirement_analysis.py`.

## Task Decomposition

The Task Decomposer converts an analyzed requirement into a reviewable plan: tasks with type, dependencies, execution sequence, acceptance criteria, requirement traceability, expected AI-assistance category, and risks. **Ambiguity gate:** a `HIGH`-impact unresolved ambiguity blocks generation entirely — verified live in Phase 10 (0 tasks, `status: "BLOCKED"`) and re-demonstrable on demand via the Scenarios screen.

## AI-Assisted Development

Used task-by-task via `AIProvider.complete_structured()` — never as a whole-system generator. Every meaningful interaction is logged in [AI_USAGE.md](../AI_USAGE.md) (10 entries, TASK-001 through TASK-010), including mistakes: a real lost-update race found during Phase 9's "after" measurement (not assumed favorable), a shared-test-database isolation gap found by actually running Phase 11's new tests, and a dependency-pin conflict discovered in Phase 12 before an upgrade was attempted, not after.

## Engineer Review

Every AI output — task plan, per-task recommendation, generated artifact — requires an explicit `EngineerDecision` (`ACCEPT`/`MODIFY`/`REJECT`, with `rationale` required for the latter two, enforced at the schema level so a client can't skip it). Structurally, not just by convention: `AIRunNotAcceptedError` blocks artifact generation from any run that isn't `ACCEPT`ed; a rejected artifact is not `VALIDATED`-eligible.

## Greenfield Scenario

The URL shortener, built from nothing, entirely through the pipeline above. See [docs/scenarios/greenfield.md](scenarios/greenfield.md); real IDs from an actual executed run in [docs/REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md).

## Brownfield Scenario

An existing (Phase 8) URL shortener with unquantified "slow" redirects. Baseline measured for real before any change; a real, code-level bottleneck identified (two sequential synchronous DB round-trips) rather than a generic "add Redis" guess; the fix deferred the click-count write to a background task. **A genuine regression was found** in the "after" measurement (498/500 clicks recorded, not 500/500) — a lost-update race the deferral introduced — and fixed with an atomic SQL increment. Net result: ~33–44% latency/throughput improvement, public API contract unchanged (verified by a dedicated regression test, not assumed). See [docs/scenarios/brownfield.md](scenarios/brownfield.md).

## Ambiguous Scenario

`"Improve the analytics."` — correctly blocked by the ambiguity gate (verified live: `status: "BLOCKED"`, 0 tasks). Three interpretations presented with trade-offs, none pre-selected. Engineer chose Interpretation C (Advanced User Analytics), which reopened an earlier privacy-minimalism decision (ADR-004) and was implemented with its own privacy mitigations (hashed IP, honest-not-fabricated geography) rather than treating the broader scope as license to be careless. See [docs/scenarios/ambiguous.md](scenarios/ambiguous.md).

## Artifact Generation

`ArtifactGenerator` turns an accepted AI recommendation into typed, real-content artifacts (`SOURCE_CODE`/`API_CONTRACT`/`DATABASE_SCHEMA`/`TEST`/`DOCUMENTATION`/`CONFIGURATION`/`ARCHITECTURE`), written only inside the sandboxed `generated/` workspace (`app.utils.safe_path`, two independent containment checks, tested against absolute paths, `..` traversal, and mid-path traversal — both at the unit level and the API level). Regeneration versions rather than overwrites (`supersedes_artifact_id`), with a diff computed at read time.

## Validation

Seven allowlisted types (`UNIT_TEST`/`INTEGRATION_TEST`/`STATIC_ANALYSIS`/`API_CONTRACT`/`BUILD`/`SECURITY`/`PERFORMANCE`), each mapped to exactly one hardcoded command — never a raw command from the API. `NOT_VALIDATED` is a real, distinct status from `PASSED`, enforced in both the backend model and the frontend UI (explicit visual distinction, tested in `frontend/src/screens/ValidationScreen.test.tsx`).

## Security

Phase 12's full review: no SQL/command injection surface exists (parameterized queries, argument-list-only subprocess calls); path traversal hardened and tested; SSRF-adjacent open-redirect risk mitigated (scheme allowlist, private/internal IP blocking); AI prompt injection bounded architecturally (untrusted content confined to the user-prompt turn; no AI output auto-trusted regardless); secrets are environment-variable-only, never logged. **Real, disclosed gaps, not fixed:** no authentication/authorization anywhere; no rate limiting anywhere; `starlette`/`pytest` carry 10 known advisories, 9 of 10 confirmed non-exploitable given this codebase's actual usage patterns (verified by reading the code, not assumed), upgrade deferred with rationale (see [ADR-006](adr/ADR-006-dependency-upgrade-deferral.md)). Full detail: [docs/security.md](security.md).

## Performance

Real measurements only, via `app/services/performance_probe.py` against a live server. Sequential: create ~970 req/s, redirect ~668 req/s, advanced-analytics ~378 req/s (all p50 sub-2.3ms). **Concurrent (new in Phase 12):** 20 threads, 300 requests against one short code — 300/300 succeeded, click-count delta matched exactly (0 lost updates), closing a gap Phases 8–9 explicitly left `NOT VALIDATED`. All numbers are SQLite-on-loopback; PostgreSQL and multi-process concurrency remain untested. Full detail: [docs/performance.md](performance.md).

## Trade-offs

* **SQLite over PostgreSQL for this environment** — zero external dependencies, at the cost of every measured number being non-representative of the proposed production database.
* **No cache (Redis)** — deferred without a traffic number to justify it (ADR-003), rather than added speculatively.
* **No authentication** — appropriate for a local, single-engineer prototype; would block any real deployment.
* **Dependency upgrade deferred** — chose not to risk an untested FastAPI major-version bump under this pass's time constraints, over closing currently-inapplicable CVEs immediately (ADR-006).
* **Backend enum kept authoritative over the master prompt's suggested UI vocabulary** — avoided a data-model rename for a UI-only concern (AI_USAGE.md TASK-009).

## Assumptions

* No live AI provider would be configured in this environment at any point — held true through all 12 phases; every "AI" response is `FakeAIProvider`'s engineer-authored stand-in, disclosed consistently rather than presented as live model output.
* A single-engineer, local-demo deployment shape — informs the "no auth, no rate limiting, hardcoded CORS origin" decisions, which would need revisiting for any other deployment shape.
* SQLite's behavior (including its file-level write serialization observed in the Phase 12 concurrency test) is treated as this environment's actual behavior, not as a stand-in for PostgreSQL's different locking model.

## Limitations

* No authentication/authorization or rate limiting anywhere (disclosed, not fixed).
* PostgreSQL, Redis, and Docker are present in the codebase (config support, compose file, Dockerfiles) but never actually deployed or exercised in this environment.
* No browser automation tool is available in this environment — every frontend behavior claim is backed by RTL/jsdom component tests plus live API-level smoke tests, never actual rendered-pixel or click-through browser verification.
* `AnthropicProvider` has zero live-API test coverage — implemented against the real SDK, never called with a real key.

## NOT VALIDATED

Consolidated from every phase, not just this report's own claims:

* Live AI provider behavior (Anthropic API never actually called).
* PostgreSQL-specific behavior of any query, including the atomic click-count `UPDATE`.
* Multi-process/multi-worker concurrent write behavior (only single-process thread concurrency tested).
* Redis-backed caching (not implemented).
* Docker build/run (Docker not installed in this environment).
* Actual browser rendering/interaction (no browser automation tool available).
* Device/browser User-Agent classifier accuracy at scale (only a handful of strings tested; disclosed as a heuristic).
* Legal/compliance review of the advanced-analytics data collection.
* Security scanning beyond `pip-audit`/`npm audit`/a heuristic secret-pattern scan — no penetration test, no SAST/DAST tool run.
* Sustained/soak-load performance (all measurements are short bursts, not sustained load over minutes/hours).

## AI Mistakes and Corrections

Representative examples (full list in [AI_USAGE.md](../AI_USAGE.md)):

* **Phase 9 (brownfield):** first "after" fix deferred a write to a background task; the actual re-measurement (not assumed favorable) showed 498/500 clicks recorded — a lost-update race not anticipated in the plan. Root-caused to Python-side read-modify-write; corrected to a single atomic SQL `UPDATE`.
* **Phase 11 (UI):** built the Artifact screen against the master prompt's suggested status vocabulary before checking it against the real backend enum; caught the mismatch, kept the backend authoritative, added a display-only mapping instead. Separately, `npm run test` initially failed 13/19 due to a missing RTL cleanup wire-up (not obvious until actually running the tests) plus three independent test-assertion bugs — all found and fixed by running the tests, not by inspection alone.
* **Phase 12 (hardening):** first instinct on finding 10 `pip-audit` advisories was to upgrade the vulnerable packages directly; checking the dependency pin first revealed that would require a much larger, unvalidated FastAPI upgrade — deferred with a documented rationale (ADR-006) instead of either ignoring the finding or rushing an untested fix.

## Final Engineering Assessment

**What this prototype demonstrates well:** a real, working, traceable pipeline where AI participates in engineering without being trusted by default — every gate (task acceptance, AI-run acceptance, artifact acceptance, the ambiguity block) is enforced in code and independently tested, not just described in documentation. The brownfield and ambiguous scenarios in particular show the project's stated values in practice: a real regression reported rather than hidden, and a genuinely blocked implementation rather than a superficial "asked for clarification" gesture.

**What it does not demonstrate:** production readiness. No authentication, no rate limiting, an unexercised PostgreSQL path, and zero live-AI-provider coverage are real, current gaps — not oversights, but they are gaps. This project should be assessed as a working demonstration of an engineering *process*, not as a deployable service.
