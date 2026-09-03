# Architecture

**Status: implemented and deployed.** The Requirement Analyzer, Task Planner / Engineer Review, task-level AI Assistance, controlled Artifact Generation, the Validation Engine, the mandatory URL Shortener use case, the brownfield and ambiguous scenarios, and a full end-to-end UI all exist and are running.

**AI never modifies the repository outside the sandboxed `generated/` workspace, executes commands, or applies its own output without an explicit engineer Accept/Reject at every stage.**

A few things worth knowing before the component list below:

* **The URL shortener is built *through* this workbench**, not a disconnected app in the same repo — its requirement, analysis, and task plan were processed by the same Requirement Analyzer / Task Decomposer described below. See `backend/tests/test_url_shortener_workbench_flow.py` for a permanent, re-runnable proof.
* **A brownfield scenario runs the same pipeline against existing code** (a redirect-performance optimization) — including a real lost-update regression that was found and fixed, not glossed over. Full before/after numbers in README.md §7.
* **An ambiguous-requirement scenario shows the workbench refusing to guess.** *"Improve the analytics."* was blocked (0 tasks) until the engineer chose one of three presented interpretations. See Key Design Decisions below for the privacy mitigations that followed.
* **The AI provider integration has been exercised against the live Anthropic API**, not only a fake stand-in — see README.md §8 and §11 for the two real defects this surfaced and fixed.

## System Purpose

Take a software requirement as input and, through an engineer-driven, AI-assisted workflow, produce reviewed and validated engineering artifacts — code, API contracts, database schemas, tests, documentation. AI participates within individual tasks; the engineer reviews and controls what gets accepted at every stage.

## High-Level Architecture

```text
                         ENGINEER
                            │
                            ▼
                     React + TypeScript UI
                            │
                            ▼
                       FastAPI backend
                            │
             ┌──────────────┼──────────────┐
             ▼              ▼              ▼
       Requirement       Task Planner    Validation
         Analyzer                         Engine
             │              │              │
             └──────────────┼──────────────┘
                            ▼
                     AI Assistance
                    (Anthropic, live)
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
                  SQLite (dev) / PostgreSQL (Render, live)
```

## Components

**Web UI** — `frontend/src/components/AppShell.tsx` hosts navigation (Dashboard/Requirement/Engineering Plan/Tasks/AI Runs/Artifacts/Validation/Scenarios/Final Report) plus a project selector. `frontend/src/hooks/useProjectData.ts` assembles one consistent snapshot per requirement so every screen reads the same data. Task-artifact and artifact-validation fetches run concurrently (`Promise.all`), not sequentially — a live-usage session showed the sequential version making 40+ round trips on a single reload.

**Backend API** — FastAPI service layer coordinating the UI, the analysis/planning components, the AI assistance layer, and persistence.

**Requirement Analyzer** — interprets an incoming requirement into a structured understanding: summary, functional/non-functional requirements, ambiguities, assumptions, constraints, success criteria, engineering concerns. `RequirementAnalyzer` (`backend/app/services/requirement_analyzer.py`), behind `POST /api/v1/requirements/{id}/analyze`.

**Ambiguity Detector** — not a separate pipeline stage. The analyzer's output schema has a dedicated `ambiguities` field distinct from `assumptions`, so detection is a property of the output contract. Ambiguities are surfaced to the engineer, never silently resolved.

**Task Planner** — converts an analyzed requirement into an engineer-reviewable plan: tasks with types, dependencies, sequence, acceptance criteria, requirement traceability, expected AI-assistance category, risks. `TaskDecomposer` (`backend/app/services/task_decomposer.py`), behind `POST /api/v1/requirements/{id}/tasks`. Two enforcement mechanisms:
* **Ambiguity gate** — a `HIGH`-impact unresolved ambiguity blocks plan generation entirely (no AI call, no tasks)
* **Referential integrity** — duplicate/self/circular task dependencies and invalid requirement references are rejected before persistence, beyond what schema validation alone would catch

**AI Assistance Layer** — a provider-abstracted layer (`app.ai.base.AIProvider`) through which tasks request schema-validated output, without knowing which provider is behind it. One concrete provider: `AnthropicProvider` (`backend/app/ai/anthropic_provider.py`), selected via `AI_PROVIDER`/`AI_API_KEY`/`AI_MODEL`. The Requirement Analyzer, Task Planner, and task-level AI assistance all reuse this same abstraction. Structured output comes from a forced tool call, not free-text parsing. `max_tokens=16384` plus explicit `stop_reason` truncation detection were added after a live session found the original, smaller budget silently truncated larger responses (README.md §11).

**Engineer Review** — `POST /api/v1/tasks/{task_id}/decision`, `POST /api/v1/ai-runs/{ai_run_id}/decision`, `POST /api/v1/artifacts/{artifact_id}/decision` share one `EngineerDecision` model and ACCEPT/MODIFY/REJECT vocabulary, distinguished by which of `task_id`/`ai_run_id`/`artifact_id` is set. `reviewer` exists on the model but is always `null` — no authentication exists anywhere (documented, not silently assumed).

**AI Run** — `AIRun` (`backend/app/models/engineering_plan.py`) persists every task-level AI request: provider, model, assistance type, prompt, structured response (or `null`), status (`COMPLETED`/`FAILED`), duration, and — when following a `MODIFY` decision — `revised_from_ai_run_id`, making `AI-RUN-001 → MODIFY → AI-RUN-002` lineage queryable rather than inferred from timestamps. A **failed** run is persisted too, not discarded.

**Artifact Generator** — turns an ACCEPTed AI recommendation into concrete draft artifacts: real proposed file content, one artifact per implied file, typed (`SOURCE_CODE`/`API_CONTRACT`/`DATABASE_SCHEMA`/`TEST`/`DOCUMENTATION`/`CONFIGURATION`/`ARCHITECTURE`). `ArtifactGenerator` (`backend/app/services/artifact_generator.py`), behind `POST /api/v1/ai-runs/{ai_run_id}/artifacts`. Gated structurally: only reachable from an AI run whose latest decision is `ACCEPT` (`AIRunNotAcceptedError` → `409` otherwise).

**Controlled File Writes** — every artifact path is validated (`app.utils.safe_path.resolve_artifact_path`) before anything is written: absolute paths and `..` segments rejected outright, then the resolved path is re-checked for containment within `generated/`. One unsafe path in a batch rejects the whole batch (`422`).

**Artifact Versioning** — regenerating an artifact for the same task+path never overwrites the prior row. A new `Artifact` is inserted with `version = previous.version + 1` and `supersedes_artifact_id` pointing at the one it replaces. Both rows persist.

**Validation Engine** — runs allowlisted checks and persists the result, never a raw command from the API:

| Type | What it runs |
|---|---|
| `UNIT_TEST` / `INTEGRATION_TEST` | `pytest` |
| `STATIC_ANALYSIS` | `ruff` |
| `API_CONTRACT` | Structural OpenAPI check |
| `BUILD` | Import check |
| `SECURITY` | Static secret-pattern scan |
| `PERFORMANCE` | Always `NOT_VALIDATED` at this generic level |

`app/services/validation_runner.py` (the allowlist) + `app/services/validation_service.py`, behind `POST /api/v1/artifacts/{id}/validate`.

**Persistence** — durable storage for requirements/analyses, plans/tasks/decisions, AI runs, artifacts (`app/models/requirement.py`, `app/models/engineering_plan.py`, SQLAlchemy). SQLite is the zero-dependency local/test default; **PostgreSQL is live in production** (Render's `workbench-db`) — `DATABASE_URL` switches the dialect with no code change. No migration framework yet — `Base.metadata.create_all()` at startup is a deliberate deferral while the schema is still small, not an oversight. A `DELETE /api/v1/requirements/{id}` endpoint walks the full dependency tree leaf-to-root in one transaction (no `ON DELETE CASCADE` exists at the DB level, since the schema comes from `create_all()` rather than migrations) — added to clean up test/demo data without a database console, covered by a test that builds a full pipeline and deletes it end to end.

**Generated project workspace** (`generated/`) — the on-disk sandbox root that `app.utils.safe_path` writes are contained to. Enforced, not just a convention.

**URL Shortener** — the mandatory demonstration use case, not a component of the workbench itself: `ShortenedUrl` (`app/models/url.py`), `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`, `GET /api/v1/urls/{short_code}/analytics/advanced`. Its full chain — requirement → analysis → plan → task → AI-run → artifact → validation — was processed *through* the components above.

## Key Design Decisions

Decision → main rejected alternative → trade-off accepted, condensed from this project's engineering decision records:

**Human-in-the-loop over one-shot or autonomous generation**
* Chose: every AI run needs an explicit ACCEPT/MODIFY/REJECT before becoming an artifact
* Rejected: a single LLM call generating the whole system (no per-decision traceability); autonomous multi-agent development (review becomes optional)
* Trade-off: slower, more upfront structure — in exchange for full traceability and no silently-resolved ambiguity

**Short-code generation: random CSPRNG over sequential or UUID**
* Chose: random 7-character Base62 via `secrets.choice`, DB unique constraint detects collisions, bounded retry
* Rejected: sequential/auto-increment (enumerable — a real privacy defect); UUID4 (too long, and truncating reintroduces collision risk)
* Trade-off: 62⁷ ≈ 3.5 trillion combinations makes collisions negligible — in exchange for a bounded-retry loop instead of an upfront guarantee

**No cache layer yet**
* Chose: `GET /{short_code}` stays a direct indexed DB query; revisit once traffic volume is an actual number
* Rejected: in-process LRU (doesn't share state across instances); Redis speculatively (unrequested infrastructure, no number to size it against)
* Trade-off: simplicity now — in exchange for deferred scaling headroom

**Minimal analytics by default**
* Chose: track only `click_count` and `last_accessed_at` — no per-click event table, no geo/device/referrer, unless an engineer explicitly asks for more
* Rejected: a per-click event table from the start (unbounded growth, no retention policy, unrequested)
* Trade-off: privacy-by-minimalism, no unbounded storage growth — in exchange for not being able to reconstruct historical per-click detail later

**Advanced analytics only on explicit engineer choice, with privacy mitigations**
* When the ambiguous "improve the analytics" requirement was resolved toward the richest interpretation, three unrequested-but-necessary mitigations were added:
  * IP addresses salted-hashed, never stored raw, used only for repeat-visitor detection
  * Geographic data honestly reported as unavailable rather than fabricated
  * User-agent strings reduced to coarse categories, raw string never returned
* Trade-off: hashing the IP forecloses ever retroactively adding real geo-resolution — accepted deliberately over storing raw IPs

**Deferred a dependency security-advisory upgrade rather than rushing it**
* `pip-audit` found 10 advisories against `starlette`/`pytest`; the real fix requires a `starlette` version the pinned FastAPI release doesn't support
* Chose: verify each advisory's actual applicability (9 of 10 use code paths not present here), document the upgrade as a tracked follow-up
* Rejected: an unvalidated major FastAPI bump under time pressure
* Trade-off: one currently-inapplicable vulnerability class stays open on paper — in exchange for not risking an untested breaking change

## Security Boundaries

Where trust boundaries actually sit (full review scope in README.md §12):

| Boundary | How it's enforced |
|---|---|
| Client → API | Pydantic schema validation at the edge (length caps, scheme/host allowlists, closed enums) before any service code runs |
| API → Database | SQLAlchemy ORM/Core only — no raw SQL string ever constructed from request data |
| API → Filesystem | Every artifact write contained to `generated/` by `resolve_artifact_path`, with two independent checks |
| API → Subprocess | `validation_type` is a closed enum; each maps to exactly one hardcoded, argument-list `subprocess.run` call — no code path from a request field into a shell command |
| API → AI Provider | Untrusted content lives only in the *user* prompt turn, never the *system* prompt; forced tool-call constrains responses to schema-shaped JSON. Deeper boundary: no AI output is ever auto-trusted, bounding even a successful prompt-injection attempt to "a bad recommendation for a human to reject" |
| Secrets | `AI_API_KEY` is environment-variable-only, never logged, never present in prompt content |

**Known, disclosed gaps (not fixed):** no authentication/authorization, no rate limiting — appropriate-for-scope for a demonstration prototype, not oversights. See README.md §13.

## Traceability

```text
Requirement → Task → AI Run → Engineer Decision → Artifact → Test → Validation
```

Every link except `Test` (a dedicated test-artifact-execution concept, distinct from the `UNIT_TEST`/`INTEGRATION_TEST` validation *types*, which already run real tests) is real and queryable end-to-end:

* A task's `requirement_refs` point back to specific analysis items
* Each `AIRun` links to its `task_id`
* Each `EngineerDecision` links to its `ai_run_id`/`artifact_id`/`task_id`
* Each `Artifact` links to both its `ai_run_id` and `task_id`
* Each `Validation` links to both its `artifact_id` and `task_id`

## AI-Human Interaction

```text
AI Recommendation → Engineer Review → Accept / Modify / Reject → Validation → Final Artifact
```

No AI recommendation becomes a final artifact without an explicit engineer decision and a validation step.

## Technology Rationale

| Choice | Why |
|---|---|
| React + TypeScript | Typed frontend suited to a review-heavy UI (diffs, accept/modify/reject actions) |
| Python + FastAPI | Strong fit for API development + AI provider SDK integration, with Pydantic typing |
| PostgreSQL | Relational database for structured, relationship-heavy data (requirements, tasks, decisions, artifacts); live in production |
| Redis | Proposed for future caching, not yet implemented — deferred until a real traffic number justifies it |
| Pytest | Standard, low-friction Python testing |
| OpenAPI | Widely supported API contract format — used both for this API and as a generatable artifact type |
| AI provider abstraction | Avoids hard-coupling to one vendor; one concrete provider (Anthropic) implemented and live |
