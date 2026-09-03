# AI Engineering Workbench

> AI-assisted software engineering workbench that transforms software requirements into structured, validated engineering artifacts with human-in-the-loop review.
>
> Demonstrated end-to-end via the mandatory use case: **build a scalable URL shortener service with APIs, persistence, and analytics.**

---

## 1. Project

A FastAPI backend and a React UI that take a plain-English requirement and carry it through:

* Requirement analysis
* Task decomposition
* AI-assisted execution
* Engineer review
* Artifact generation
* Validation

Every step is persisted and traceable back to the requirement that motivated it. This has been run against the **real Anthropic API** end-to-end, not only a fake stand-in provider — see §8 and §11.

## 2. Problem

Teams using AI to accelerate development often do it in an unstructured, unauditable way:

* Prompts are ad hoc
* Outputs are accepted without review
* There's no record of what the AI got wrong or how an engineer corrected it

This project demonstrates a different workflow. AI participates *within* individually-scoped tasks — never as a one-shot generator of the whole system. Every AI output passes through an explicit, recorded engineer decision (`ACCEPT` / `MODIFY` / `REJECT`) before it has any effect.

## 3. Philosophy

> **AI assists the engineer within tasks; the engineer owns execution and quality.**

This is enforced structurally, not just by convention:

* No AI recommendation can generate an artifact until it's been `ACCEPT`ed (`AIRunNotAcceptedError` → `409` otherwise)
* No artifact is `VALIDATED`-eligible until an engineer `ACCEPT`s it
* Validation only ever runs a fixed, allowlisted command per type — never a raw command string from a request
* A `HIGH`-impact unresolved ambiguity blocks task decomposition entirely (0 tasks, `status: "BLOCKED"`) rather than letting the planner guess
* `AIRun.status` / `Validation.status` distinguish `FAILED` / `NOT_VALIDATED` from success — a missing or failed check is never presented as a pass

This project is never described as autonomous software development. AI is a recommendation source; the engineer decides at every gate.

## 4. Architecture

```text
Engineer
   → UI (React + TypeScript, 9 screens)
   → Requirement Analyzer     (FR/NFR/ambiguities/assumptions/constraints/risks)
   → Engineering Planner      (decomposes into tasks; blocks on HIGH-impact ambiguity)
   → AI Assistance            (provider-abstracted, schema-validated recommendations per task)
   → Engineer Review          (ACCEPT / MODIFY / REJECT — at task, AI-run, and artifact stages)
   → Artifact Generator       (writes real proposed file content into a sandboxed workspace)
   → Validation Engine        (allowlisted UNIT_TEST/STATIC_ANALYSIS/API_CONTRACT/BUILD/SECURITY/PERFORMANCE)
   → Final Report             (aggregated summary, exportable)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component breakdown, data flow, security boundaries, and design decisions.

## 5. Technology Stack

Only what's actually present and used — nothing aspirational listed as current.

| Layer | Technology | Status |
|---|---|---|
| Backend | Python 3.12/3.13, FastAPI, SQLAlchemy 2.0, Pydantic v2 | Implemented |
| Frontend | React 19, TypeScript, Vite 8 | Implemented |
| Frontend testing | Vitest, React Testing Library | Implemented |
| Backend testing | pytest, ruff | Implemented — 188 tests |
| Database (dev/test) | SQLite | Implemented, actually used |
| Database (production) | PostgreSQL | **Live** — Render's `workbench-db`, exercised by the real backend |
| Cache | Redis | Not implemented — deferred without a traffic number to size it |
| AI provider | Anthropic SDK, behind a provider-agnostic `AIProvider` interface | **Live** — see §8 |
| Containerization | Docker | Backend Dockerfile is the real Render deployment artifact |
| API contract | OpenAPI (auto-generated, structurally validated) | Implemented |

## 6. Mandatory Use Case

> **Build a scalable URL shortener service with APIs, persistence, and analytics.**

**Endpoints:** `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`, `GET /api/v1/urls/{short_code}/analytics/advanced`

**Built through the workbench, not alongside it.** Its own requirement was:

1. Registered and analyzed via the Requirement Analyzer
2. Decomposed via the Task Decomposer
3. Routed through AI-assist → engineer review → artifact generation → artifact review → real validation

See `backend/tests/test_url_shortener_workbench_flow.py` for the permanent, re-runnable proof, and §11 for the live-API run of this exact sentence.

**Key decisions** (full reasoning and rejected alternatives in ARCHITECTURE.md):
* CSPRNG Base62 short codes with DB-enforced collision retry
* No cache yet — tied to an unresolved traffic-volume ambiguity, not an oversight
* Minimal analytics by default (click count + last-accessed timestamp only), extended only on explicit engineer choice

## 7. Demonstration Scenarios

All three are demonstrable live in the UI's **Scenarios** screen, and each has a `FakeAIProvider`-backed integration test for repeatability.

### Greenfield — built from nothing

> *"Build a scalable URL shortener service with APIs, persistence, and analytics."*

* One ambiguity surfaced (traffic volume never quantified) but didn't block planning
* Task Decomposer produced 4 tasks: short-code generation, URL persistence + redirect, click analytics, advanced analytics
* Each task: Accept → AI-assist → Accept → artifact generation → artifact review → validation
* Later concurrent-load test: 300 concurrent requests against the redirect endpoint, **0 lost clicks**

### Brownfield — a real regression, not a staged one

> *"The existing URL shortener has slow redirect performance. Improve performance without changing the public API."*

* Baseline: p50 0.98ms / p95 1.19ms / p99 1.48ms / 990 req/s
* AI's first recommendation (defer click-count write to a background task) was sound, but the engineer issued a `MODIFY` requiring a regression test that pins the exact response contract first
* After the accepted revision, the **first "after" measurement found a real bug**: 498/500 clicks recorded — a lost-update race from a non-atomic read-modify-write
* Fixed with an atomic SQL `UPDATE ... SET click_count = click_count + 1`; re-measured at 500/500
* Final: p50 0.66ms / p95 0.78ms / p99 1.14ms / 1422 req/s — ~33% faster p50, ~44% higher throughput, API contract unchanged (test-verified)

### Ambiguous — refusing to guess

> *"Improve the analytics."*

* Ambiguity gate correctly returned `status: "BLOCKED"`, 0 tasks — "no analytics system or desired improvement is named" rated HIGH impact
* Three interpretations presented: scheduled reporting, real-time dashboards, or advanced per-visitor analytics
* Engineer chose the third
* Implementation added privacy mitigations that weren't asked for but were judged necessary:
  * IP addresses salted-hashed, never stored raw, used only for repeat-visitor detection
  * Geographic data honestly reported as unavailable rather than fabricated
  * User-agent strings reduced to coarse device/browser categories, raw string never returned

## 8. AI Provider Configuration

`AnthropicProvider` (`backend/app/ai/anthropic_provider.py`) targets the real Anthropic Messages API — set via `AI_PROVIDER=anthropic` / `AI_API_KEY` / `AI_MODEL` (see `.env.example`).

**It has now been exercised against the live API end-to-end** for the mandatory use case, closing what was previously a standing `NOT VALIDATED` item. Doing so surfaced two real defects that `FakeAIProvider`-only testing structurally could not catch (full story in §11):

1. A `max_tokens` budget too low for larger structured outputs
2. A response where the model double-encoded one field as a JSON string instead of native JSON

Both are now covered by `backend/tests/test_anthropic_provider.py` — mocked-client unit tests, so this coverage doesn't depend on repeatedly spending a live API budget.

## 9. Setup Guide

### Prerequisites

* Python 3.12+ (3.13 verified working; 3.14 has no compatible `pydantic-core` wheel at the pinned version yet)
* Node.js 22+ / npm
* No PostgreSQL, Redis, or Docker required locally — SQLite is the zero-dependency default

### Environment Variables

```bash
cp .env.example .env
```

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | No | Defaults to local SQLite. Accepts `postgres://`/`postgresql://`/`postgresql+psycopg://` — the first two auto-normalize to the psycopg3 driver. |
| `REDIS_URL` | No | Unused — no code path reads it yet. |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins. |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | Only for `/analyze` and AI-assist | Without these, those endpoints return a clean `503`. |
| `VITE_API_BASE_URL` | No | Frontend's backend URL; defaults to `http://localhost:8000`. |
| `IP_HASH_SALT` | No | Salts the IP hash for repeat-visitor detection; random per process if unset. |

**Never commit a real `.env`** — it's git-ignored; `.env.example` holds only empty placeholders.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

`GET /health` → `{"status": "ok"}`. OpenAPI docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173).

### Deploying to Render

`render.yaml` defines a Blueprint: backend as a Docker web service, frontend as a static site, managed PostgreSQL. **This is deployed and live** — `workbench-backend`, `workbench-frontend`, and `workbench-db` are all running, with the backend actually exercising the Postgres path.

1. Render dashboard → **New → Blueprint** → connect this repo
2. `AI_API_KEY` is deliberately **not** in `render.yaml` (`sync: false`) — set it manually on the backend service
3. `DATABASE_URL` wires automatically from the Postgres instance

**Disclosed limitations:** no CI/CD, no staging environment, no rollback strategy beyond Render's deploy history. Free-tier services can have a slow first request after idling (cold start) — observed directly during live testing, not a code defect.

### Running Tests

```bash
# Backend
cd backend && source .venv/bin/activate && pytest -v && ruff check .

# Frontend
cd frontend && npm run test && npm run build && npm run lint
```

## 10. Repository Structure

```text
ai-engineering-workbench/
├── README.md, ARCHITECTURE.md
├── .env.example, docker-compose.yml, render.yaml
│
├── backend/            # FastAPI app — see backend/README.md
│   ├── app/            # models, schemas, services, repositories, api/routes, ai/
│   └── tests/          # pytest suite (188 tests)
│
├── frontend/           # React + TypeScript app
│   └── src/
│       ├── screens/    # Dashboard, Requirement, Plan, Tasks, AI Runs, Artifacts, Validation, Scenarios, Final Report
│       ├── hooks/       # useProjectData, workflowStage
│       ├── api/         # typed fetch clients
│       └── components/ # AppShell + shared pieces
│
└── generated/          # Sandboxed workspace for AI-generated artifacts
```

## 11. AI-Assisted Development

AI is used task-by-task, never as a whole-system generator — one provider-abstracted interface (`AIProvider`) shared by requirement analysis, task decomposition, task-level assistance, and artifact generation.

Every meaningful AI interaction was logged with the same structure: what was asked → what came back → what the engineer found wrong → how it was corrected → how that was validated → final ACCEPT/MODIFY/REJECT. Selected entries, in build order:

**Requirement Analyzer** — the AI-provider dependency was resolved before checking whether the requirement existed, so a 404 case returned a misleading AI-config error. Fixed by building the dependency lazily, after existence is confirmed.

**Task Decomposer** — the AI's task graph needed a referential-integrity layer beyond schema validation: duplicate/self/circular dependencies, invalid requirement references. Added dedicated engineer-authored validation with a unit test per failure mode.

**AI-assist lineage** — a `MODIFY` decision now explicitly links the next run via `revised_from_ai_run_id`, so `AI-RUN-001 → MODIFY → AI-RUN-002` is queryable, not inferred from timestamps.

**Artifact generation prompt fix** — an early prompt caused the AI to emit JavaScript test files even though the validation runner only executes Python (`pytest`). Corrected to require pytest-style Python tests.

**Frontend build** — the AI built the UI against a plausible-but-wrong Artifact status vocabulary instead of the real backend enum (`PENDING_REVIEW`/`APPROVED`/`NEEDS_REVISION`/`REJECTED`). Kept the real enum authoritative; added a display-only label instead of changing the data model.

**Dependency-upgrade caution** — `pip-audit` found 10 advisories; the AI's first instinct was to upgrade directly. The engineer checked FastAPI's version pin first and found the real fix would force a much larger, riskier FastAPI upgrade — deferred as a tracked follow-up instead.

**Live-API validation (this session)** — running the mandatory requirement through the *real* Anthropic API (previously only `FakeAIProvider`) surfaced two defects in one sitting:

* **Truncation.** `max_tokens=4096` silently truncated task-decomposition output once a plan had more than a couple of tasks. The truncated JSON then failed schema validation with a confusing "Field required" error instead of a clear truncation signal. Raised progressively to 16384 once artifact generation (full multi-file content in one response) needed even more headroom, and added an explicit `stop_reason == "max_tokens"` check so this fails legibly from now on.
* **Double-encoding.** For one large, text-heavy response, the model wrapped a field as a JSON *string* instead of native JSON. Added a narrow, tested fallback that detects and unwraps this specific shape.

Both are covered by `backend/tests/test_anthropic_provider.py` (7 tests, mocked client, no ongoing API cost) — `AnthropicProvider` previously had zero test coverage. The live run then completed successfully: a fresh requirement was analyzed, clarified past its ambiguity gate, decomposed into a 13–16 task plan (varies run to run — AI output isn't deterministic), and one task was carried through AI-assist → artifact generation, producing real multi-file source and test code.

**Frontend performance (this session)** — after the live run above, the UI was slow after every Accept. Root cause: `useProjectData`'s reload fetched every task's artifacts, then every artifact's validations, **sequentially** — with a 16-task plan and one task holding 25 artifacts, that was 41+ round trips done one at a time. Fixed by parallelizing both loops with `Promise.all`; wait time is now bounded by the slowest single call, not the sum of all of them.

## 12. Validation and Testing Approach

Nothing here is claimed as tested unless it was actually executed; `NOT VALIDATED` is used literally wherever something wasn't run.

**What was actually run:**

| Area | Result |
|---|---|
| Backend tests | `pytest -v` → 188/188 passing |
| Backend lint | `ruff check .` → clean |
| Frontend build | Clean, no type errors |
| Frontend tests | A few pre-existing `AppShell`/`ScenariosScreen` assertions fail after an earlier UI redesign changed the empty-project state — a test-maintenance gap, not a functional regression (confirmed via `git stash` comparison: identical failures with or without unrelated changes) |
| API contract | Live OpenAPI schema structurally checked by the `API_CONTRACT` validation type |
| Scenarios (§7) | Each has a `TestClient` + `FakeAIProvider` integration test; the greenfield/mandatory scenario has *also* run against the live Anthropic API directly — fast deterministic tests for regression coverage, plus one real run as ground truth |

**Security review** — 14 areas covered:
* Authentication: none — disclosed, not fixed
* SQL/command injection: no surface (ORM-only queries; closed-enum validation runner mapped to hardcoded commands)
* Path traversal: hardened and tested (`../../.env`-style payloads rejected)
* SSRF/open-redirect: scheme allowlist, private/loopback/reserved-IP blocks
* Secrets: env-var only, never logged
* Dependency scan: `pip-audit` found 10 advisories against `starlette`/`pytest` — 9 of 10 use code patterns not present here, the 10th is local-only dev-time. Upgrade deferred as a tracked follow-up rather than rushed (fix would force a much larger FastAPI bump).

**Performance** — measured, not estimated:
* Sequential: ~970 req/s (create), ~668 req/s (redirect), SQLite/loopback
* Concurrent: 20-thread load test against redirect, 300/300 successful, click counter delta matched exactly — **0 lost updates**, closing a gap earlier scenarios had left open

**Known limitations, disclosed rather than hidden:**
* No authentication, authorization, or rate limiting on any endpoint
* PostgreSQL is live; Redis/caching remains unimplemented
* No dependency-vulnerability scanning beyond the one pass above; no SAST/DAST or pen test
* Frontend verified via component tests + API smoke checks, not full browser-automation E2E
* No multi-worker/multi-process concurrent-write load test against Postgres — only single-process thread concurrency against SQLite

## 13. Risk Awareness

**Functional and design risks:**
* No authentication anywhere — every endpoint is public. Fine for a local/demo prototype, not for production without adding it.
* No rate limiting — AI-assist and analysis endpoints could exhaust API budget if exposed publicly without a gateway.
* Short-code generation relies on a DB unique constraint + bounded retry, not pre-reservation. Untested at extreme write concurrency, though no issue at the concurrency levels actually measured.

**AI-related risks, observed directly rather than assumed:**

| Risk | What happened | Mitigation |
|---|---|---|
| Incorrect/incomplete output under token pressure | `max_tokens` truncation (§11) cut a response off mid-structure; the resulting error didn't make the cause obvious | Generous budget for known-large responses + explicit `stop_reason` check that fails loudly and specifically |
| Non-deterministic output shape | The same schema, requested twice, wasn't encoded the same way — one response double-encoded a field as JSON text | Defensive unwrapping for this specific shape, backed by a test pinning the exact failure mode |
| Prompt-injection-adjacent risk | The AI's own response flagged that a task's "assumptions" text block could be mistaken for an instruction, and said explicitly it was treating it as data | Schema-containment (untrusted content confined to user-prompt turn) worked here — but the real backstop is architectural: no AI output is ever auto-trusted, regardless of how well-behaved one response looks |
| Inefficiency | A generation attempt that fails halfway still consumes API budget and time before the failure surfaces | Regression tests for both bugs above run against a mocked client — no live call needed to verify the fix |

**Trade-offs made explicitly, not silently:**
* Human-in-the-loop review at every stage over a faster one-shot/autonomous approach — slower per task, fully traceable, no silently-resolved ambiguity
* Deferred caching and the `starlette`/`fastapi` security-advisory upgrade rather than rush either under time pressure — tracked as open follow-ups
* Minimal analytics by default, expanded (with privacy mitigations) only on explicit engineer choice

## 14. Final Engineering Output

**Implementation approach.** Every requirement flows through the same five-stage pipeline — analysis → planning → AI-assist → artifact generation → validation — regardless of whether it's greenfield, brownfield, or ambiguous. What changes is which *gates* fire: the ambiguity gate blocks ambiguous requirements; brownfield work modifies existing code behind a contract-stability test instead of creating new files. One pipeline, one audit trail, no special-cased logic per requirement type.

**Generated artifacts.** Typed (`SOURCE_CODE`/`TEST`/`DOCUMENTATION`/`ARCHITECTURE`/etc.), written into the sandboxed `generated/` workspace, versioned on regeneration — never overwritten. The live session (§11) produced real multi-file source and test code for the URL shortener's create-endpoint task, via the exact same path as every `FakeAIProvider`-backed test.

**Risks and validation.** Covered in §12–13 — validation states plainly what wasn't run, and risk awareness extends to AI-specific failure modes actually observed in this build, not generic security boilerplate.

**Assumptions and limitations.** This is a working demonstration of an engineering *process* — requirement understanding, engineer-led decomposition, gated AI assistance, real validation — not a fully hardened, production-deployed service. The biggest gaps toward real production traffic: no authentication, no rate limiting, no multi-worker Postgres load testing. All disclosed above, not glossed over.

## 15. Git Workflow

Small, phase-scoped commits — each one a coherent change (a bug fix, a feature, a doc pass) with tests run and passing before the commit is made. Never committed automatically without verification first.

## 16. Current Status

* Core pipeline (requirement → analysis → plan → tasks → AI-assist → artifacts → validation): **implemented, tested (188 backend tests)**
* Exercised via a fast deterministic fake provider (three demonstration scenarios) **and** the real live Anthropic API (mandatory use case) — the live run surfaced and fixed two genuine defects the fake-provider tests alone couldn't catch
* Backend + frontend deployed and running on Render, backed by real PostgreSQL
* Known gaps — no auth, no rate limiting, Redis unexercised, limited load testing — disclosed in §12–13, not hidden
