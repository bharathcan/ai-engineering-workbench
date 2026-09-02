# Architecture

> **Status: Partially implemented.** The Requirement Analyzer (Phase 3), Task Planner / Engineer Review (Phase 4), task-level AI Assistance (Phase 5), controlled Artifact Generation (Phase 6), the Validation Engine (Phase 7), the mandatory URL Shortener use case (Phase 8), a brownfield performance optimization against it (Phase 9), and an ambiguous-requirement scenario resolved by explicit engineer decision (Phase 10) all exist — see the Components section below for what's real vs. still proposed. **AI never modifies the repository outside the sandboxed `generated/` workspace, executes commands, or applies its own output without an explicit engineer Accept/Reject in every phase implemented so far** — see [docs/api-design.md](docs/api-design.md) "No Automatic Code Execution" and "Controlled File Writes".
>
> **The URL shortener (Phase 8) is a demonstration use case built *through* this workbench** — its requirement, analysis, and task plan were processed by the same Requirement Analyzer / Task Decomposer above, its create-URL task was routed through AI-assist → engineer review → artifact generation → artifact review → validation (see `backend/tests/test_url_shortener_workbench_flow.py`, a permanent, re-runnable proof of that chain) — it is not a disconnected application that happens to live in the same repository. See [docs/api-design-url-shortener.md](docs/api-design-url-shortener.md) for its own API surface, and `docs/adr/ADR-002` through `ADR-004` for its engineering decisions.
>
> **Phase 9 demonstrates the same pipeline against existing code** (a brownfield redirect-performance optimization, not a greenfield build) — see [docs/scenarios/brownfield.md](docs/scenarios/brownfield.md) for the full before/after narrative, including a real regression the optimization introduced and how it was found and fixed.
>
> **Phase 10 demonstrates the workbench refusing to guess.** "Improve the analytics." was correctly blocked by the Task Decomposer's ambiguity gate (0 tasks generated) until the engineer explicitly chose one of three presented interpretations (Advanced User Analytics). Only then was it implemented — with its own privacy-conscious engineering decision, since that choice directly reopened [ADR-004](docs/adr/ADR-004-analytics-design.md)'s minimal-data-collection reasoning — see [ADR-005](docs/adr/ADR-005-advanced-analytics-privacy.md).

## System Purpose

The workbench takes a software requirement as input and, through an engineer-driven, AI-assisted workflow, produces reviewed and validated engineering artifacts: code, API contracts, database schemas, tests, and documentation. The system is structured so that AI participates within individual tasks, while the engineer reviews and controls what gets accepted at every stage.

## High-Level Architecture

> The diagram below is a **proposed architecture concept**. Nothing shown here has been implemented.

```text
                         ENGINEER
                            │
                            ▼
                       Web UI
                            │
                            ▼
                      FastAPI API
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Requirement       Task Planner    Validation
         Analyzer                         Engine
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     AI Assistance
                         Layer
                            │
                            ▼
                     Engineer Review
                            │
                     Accept / Modify /
                         Reject
                            │
                            ▼
                    Artifact Generator
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
             Code         Tests         Docs
               │            │            │
               └────────────┼────────────┘
                            ▼
                       PostgreSQL
```

## Components

* **Web UI** — the engineer-facing interface (proposed: React + TypeScript) used to submit requirements, review AI output, and make accept/modify/reject decisions.
* **Backend API** — the service layer (proposed: FastAPI) coordinating requests between the UI, the analysis/planning components, the AI assistance layer, and persistence.
* **Requirement Analyzer** *(implemented, Phase 3)* — interprets an incoming requirement and produces a structured understanding of what is being asked: summary, functional/non-functional requirements, ambiguities, assumptions, constraints, success criteria, and engineering concerns. Implemented as `RequirementAnalyzer` (`backend/app/services/requirement_analyzer.py`), behind the `POST /api/v1/requirements/{id}/analyze` endpoint — see [docs/api-design.md](docs/api-design.md).
* **Ambiguity Detector** *(implemented as part of the Requirement Analyzer, not a separate component)* — the analyzer's structured output schema has a dedicated `ambiguities` field distinct from `assumptions`, so ambiguity detection is a property of the analyzer's output contract rather than a separate pipeline stage. Ambiguities are surfaced to the engineer in the response, not silently resolved.
* **Task Planner** *(implemented, Phase 4)* — converts an analyzed requirement into a structured, engineer-reviewable engineering plan: tasks with types, dependencies, execution sequence, acceptance criteria, requirement traceability, expected AI-assistance category, and risks. Implemented as `TaskDecomposer` (`backend/app/services/task_decomposer.py`), behind `POST /api/v1/requirements/{id}/tasks` — see [docs/api-design.md](docs/api-design.md). Enforces an **ambiguity gate**: a requirement analysis with a `HIGH`-impact unresolved ambiguity blocks plan generation entirely (no AI call, no tasks) rather than letting the planner silently pick an interpretation.
* **AI Assistance Layer** *(implemented for structured-output requests, Phase 3–5)* — a provider-abstracted layer (`app.ai.base.AIProvider`) through which individual tasks request schema-validated output from a model, without knowing which provider is behind it. One concrete provider exists (`AnthropicProvider`); callers select it via `AI_PROVIDER`/`AI_API_KEY`/`AI_MODEL` config, never by importing a provider class directly. The Requirement Analyzer, Task Planner, and (Phase 5) `TaskAssistant` all use this same abstraction with their own prompts/schemas — no new abstraction was introduced for task-level assistance, reusing the existing one instead (see `AI_USAGE.md` TASK-003). Each run's provider/model identity is exposed via `AIProvider.provider_name`/`model_name` (added Phase 5) so `AIRun` records reflect what actually ran. Free-form (non-structured) AI assistance is still not implemented — even Phase 5's recommendations are schema-validated, never free text.
* **Engineer Review** *(implemented for tasks — Phase 4 — and for AI run recommendations — Phase 5)* — `POST /api/v1/tasks/{task_id}/decision` (Phase 4) reviews a task's place in the plan; `POST /api/v1/ai-runs/{ai_run_id}/decision` (Phase 5) reviews one AI run's recommendation. Both share the same `EngineerDecision` model and ACCEPT/MODIFY/REJECT vocabulary, distinguished by whether `ai_run_id` is set — the first concrete implementation of the "Engineer Decision" node in the [traceability chain](#traceability) below, now covering both the planning stage and the AI-assistance stage. `reviewer` exists on the model but is always `null` — no authentication exists anywhere in this system (documented, not silently assumed). Not yet implemented for artifacts, since none exist yet.
* **AI Run** *(implemented, Phase 5)* — `AIRun` (`backend/app/models/engineering_plan.py`) persists every task-level AI request: provider, model, assistance type, prompt, structured response (or `null`), status (`COMPLETED`/`FAILED`), a duration measurement, and — when this run followed a `MODIFY` decision on an earlier run — `revised_from_ai_run_id`, making the `AI-RUN-001 → MODIFY → AI-RUN-002` lineage explicit and queryable rather than inferred from timestamps. Unlike the Requirement Analyzer/Task Planner (Phase 3–4), a **failed** run is persisted too, not discarded — the audit trail includes attempts that didn't produce a usable recommendation. Implemented as `TaskAssistant` (`backend/app/services/task_assistant.py`) + `app/services/ai_run_service.py`, behind `POST /api/v1/tasks/{task_id}/ai-assist`.
* **Artifact Generator** *(implemented, Phase 6)* — turns an ACCEPTed AI recommendation (Phase 5) into concrete draft artifacts: real proposed file content, one artifact per implied file, typed (`SOURCE_CODE`/`API_CONTRACT`/`DATABASE_SCHEMA`/`TEST`/`DOCUMENTATION`/`CONFIGURATION`/`ARCHITECTURE`). Implemented as `ArtifactGenerator` (`backend/app/services/artifact_generator.py`) + `app/services/artifact_service.py`, behind `POST /api/v1/ai-runs/{ai_run_id}/artifacts` — reuses the same `AIProvider` abstraction as every prior phase, with its own prompt/schema. **Gated structurally, not just by convention:** generation is only reachable from an AI run whose latest decision is `ACCEPT` (`AIRunNotAcceptedError` → `409` otherwise) — a rejected recommendation cannot become an artifact, because there is no code path that lets it.
* **Controlled File Writes** *(implemented, Phase 6)* — every proposed artifact path is validated (`app.utils.safe_path.resolve_artifact_path`) before anything is persisted or written: absolute paths and `..` segments are rejected outright, and the resolved path is re-checked for containment within `generated/` (defends against encoding/symlink tricks slipping past the first check). One unsafe path in a batch rejects the whole batch (`422`) rather than silently dropping it. See [docs/api-design.md](docs/api-design.md) "Controlled File Writes".
* **Artifact Versioning** *(implemented, Phase 6)* — regenerating an artifact for the same task+path never overwrites the prior row: a new `Artifact` is inserted with `version = previous.version + 1` and `supersedes_artifact_id` pointing at the one it replaces. Both rows, and both on-disk writes at the time each was current, persist — nothing is deleted. A unified diff against the superseded version (or against empty, for version 1) is computed at read time, not stored.
* **Engineer Review** *(implemented for tasks — Phase 4, AI run recommendations — Phase 5, and now artifacts — Phase 6)* — `POST /api/v1/tasks/{task_id}/decision`, `POST /api/v1/ai-runs/{ai_run_id}/decision`, and `POST /api/v1/artifacts/{artifact_id}/decision` all share the same `EngineerDecision` model and ACCEPT/MODIFY/REJECT vocabulary, distinguished by which of `task_id`/`ai_run_id`/`artifact_id` is set — extended again, not duplicated a third time. `reviewer` exists on the model but is always `null` — no authentication exists anywhere in this system (documented, not silently assumed).
* **AI Run** *(implemented, Phase 5)* — `AIRun` (`backend/app/models/engineering_plan.py`) persists every task-level AI request: provider, model, assistance type, prompt, structured response (or `null`), status (`COMPLETED`/`FAILED`), a duration measurement, and — when this run followed a `MODIFY` decision on an earlier run — `revised_from_ai_run_id`, making the `AI-RUN-001 → MODIFY → AI-RUN-002` lineage explicit and queryable rather than inferred from timestamps. Unlike the Requirement Analyzer/Task Planner (Phase 3–4), a **failed** run is persisted too, not discarded — the audit trail includes attempts that didn't produce a usable recommendation. Implemented as `TaskAssistant` (`backend/app/services/task_assistant.py`) + `app/services/ai_run_service.py`, behind `POST /api/v1/tasks/{task_id}/ai-assist`.
* **Validation Engine** *(implemented, Phase 7)* — runs controlled, allowlisted checks against an artifact (`UNIT_TEST`/`INTEGRATION_TEST` → `pytest`, `STATIC_ANALYSIS` → `ruff`, `API_CONTRACT` → structural OpenAPI check, `BUILD` → import check, `SECURITY` → static secret-pattern scan, `PERFORMANCE` → `NOT_VALIDATED` at this generic level) and persists the result — never a raw command from the API. Implemented as `app/services/validation_runner.py` (the allowlist) + `app/services/validation_service.py`, behind `POST /api/v1/artifacts/{id}/validate`. See [docs/validation/validation-strategy.md](docs/validation/validation-strategy.md) for exactly what each type checks and its documented limits (no dependency CVE scanning, no comprehensive security coverage).
* **Persistence** *(partially implemented, Phase 3–6)* — durable storage for requirements/analyses (Phase 3), engineering plans/tasks/engineer decisions (Phase 4), AI runs (Phase 5), and now artifacts (Phase 6) — `app/models/requirement.py`, `app/models/engineering_plan.py`, SQLAlchemy. PostgreSQL remains the proposed production database; SQLite is used as the zero-dependency local/test default (`DATABASE_URL` unset), keeping the "no required external services" property from Phase 2 — setting `DATABASE_URL` to a `postgresql+psycopg://` URL switches the dialect with no code change. No migration framework (e.g. Alembic) is introduced yet — `Base.metadata.create_all()` at startup is the smallest maintainable choice while the schema is still small and likely to change; this is a deliberate deferral, not an oversight.
* **Generated project workspace** (`generated/`) — the on-disk location where artifacts produced by the workbench are written, separate from the workbench's own source. As of Phase 6 this is no longer just a documented convention — it is the actual, enforced sandbox root that `app.utils.safe_path` writes are contained to.
* **URL Shortener** *(implemented, Phase 8)* — the mandatory demonstration use case, not a component of the workbench itself: `ShortenedUrl` (`app/models/url.py`), `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`. Its own requirement/analysis/plan/task/AI-run/artifact/validation chain was processed *through* the components above rather than hand-built outside them — see `backend/tests/test_url_shortener_workbench_flow.py`. Its own API contract is documented separately in [docs/api-design-url-shortener.md](docs/api-design-url-shortener.md), and its engineering decisions in [ADR-002](docs/adr/ADR-002-short-code-strategy.md) (short codes), [ADR-003](docs/adr/ADR-003-cache-strategy.md) (no cache yet), and [ADR-004](docs/adr/ADR-004-analytics-design.md) (minimal analytics).

## Traceability

Every artifact produced by the workbench must be traceable back to the requirement that motivated it:

```text
Requirement
→ Task
→ AI Run
→ Engineer Decision
→ Artifact
→ Test
→ Validation
```

This chain is what allows the AI usage audit (see [AI_USAGE.md](AI_USAGE.md)) and the artifact set to be reviewed together, rather than treating generated code as disconnected from why it exists.

As of Phase 7, every link except `Test` is real and queryable end-to-end: a task's `requirement_refs` point back to specific analysis items, each `AIRun` links to its `task_id`, each `EngineerDecision` links to its `ai_run_id`/`artifact_id`/`task_id`, each `Artifact` links to both its `ai_run_id` and `task_id`, and each `Validation` links to both its `artifact_id` and `task_id`. `Test` (a dedicated test-artifact-execution concept, distinct from `UNIT_TEST`/`INTEGRATION_TEST` validation *types*, which already run real tests) remains the one unimplemented, proposed link.

## AI-Human Interaction

```text
AI Recommendation
       ↓
Engineer Review
       ↓
Accept / Modify / Reject
       ↓
Validation
       ↓
Final Artifact
```

No AI recommendation becomes a final artifact without passing through an explicit engineer decision and validation step.

## Technology Rationale

The proposed technology direction is chosen for fit with the workbench's goals, not novelty:

* **React + TypeScript** — a typed frontend suited to building a review-heavy UI (diffs, accept/modify/reject actions) with reasonable tooling maturity.
* **Python + FastAPI** — a backend language and framework well suited to both API development and integration with AI provider SDKs, with strong typing support via Pydantic.
* **PostgreSQL** — a relational database appropriate for the structured, relationship-heavy data this system needs to track (requirements, tasks, decisions, artifacts) and appropriate as persistence for the URL shortener use case itself.
* **Redis** — a cache/store suited to the kind of high-throughput lookup and counting operations relevant to a URL shortener (redirect lookups, click analytics).
* **Pytest** — a standard, low-friction Python testing framework.
* **OpenAPI** — a widely supported way to define and validate API contracts, useful both for the workbench's own API and as an artifact type it can generate.
* **Docker** — standard containerization for reproducible local development and eventual deployment.
* **AI provider abstraction** — avoids hard-coupling the AI Assistance Layer to a single vendor, keeping the provider swappable.

This architecture is intentionally minimal for the current stage. It will be refined, and deviated from where justified, as implementation proceeds — over-engineering the design before any code exists would work against the workbench's own principle of engineer-reviewed, incremental progress.
