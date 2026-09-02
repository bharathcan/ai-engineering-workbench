# AI Engineering Workbench

> AI-assisted software engineering workbench that transforms software requirements into structured, validated engineering artifacts with human-in-the-loop review — demonstrated end-to-end via the mandatory use case: **build a scalable URL shortener service with APIs, persistence, and analytics.**

---

## 1. Project

`ai-engineering-workbench` is a working prototype, not a slide deck: a FastAPI backend and a React UI that take a plain-English requirement and carry it through requirement analysis, task decomposition, AI-assisted execution, engineer review, artifact generation, and validation — with every step persisted and traceable back to the requirement that motivated it. It is built in 12 completed, reviewed phases (Phases 1–12; see [AI_USAGE.md](AI_USAGE.md) for the full log and [Current Status](#14-current-status) below).

## 2. Problem

Teams using AI to accelerate development often do it in an unstructured, unauditable way: prompts are ad hoc, outputs are accepted without review, and there's no record of what the AI got wrong or how an engineer corrected it. This project demonstrates a workflow where AI participates *within* individually-scoped tasks — never as a one-shot generator of the whole system — and every AI output passes through an explicit, recorded engineer decision (`ACCEPT`/`MODIFY`/`REJECT`) before it has any effect.

## 3. Philosophy

> **AI assists the engineer within tasks; the engineer owns execution and quality.**

Concretely, this is enforced structurally, not just by convention:

* No AI recommendation can generate an artifact until it has been `ACCEPT`ed (`AIRunNotAcceptedError` → `409` otherwise).
* No artifact is `VALIDATED`-eligible until an engineer `ACCEPT`s it.
* Validation only ever runs a fixed, allowlisted command per type — never a raw command string from a request.
* A `HIGH`-impact unresolved ambiguity blocks task decomposition entirely (0 tasks, `status: "BLOCKED"`) rather than letting the planner guess.
* `AIRun.status`/`Validation.status` distinguish `FAILED`/`NOT_VALIDATED` from success — missing or failed validation is never presented as a pass.

This project never describes itself as autonomous software development. AI is a recommendation source; the engineer is the decision-maker at every gate.

## 4. Architecture

```text
Engineer
   → UI (React + TypeScript, 9 screens)
   → Requirement Analyzer     (interprets a requirement: FR/NFR/ambiguities/assumptions/constraints/risks)
   → Engineering Planner      (decomposes into tasks; blocks on HIGH-impact ambiguity)
   → AI Assistance            (provider-abstracted, schema-validated recommendations per task)
   → Engineer Review          (ACCEPT / MODIFY / REJECT — required at task, AI-run, and artifact stages)
   → Artifact Generator       (writes real proposed file content into a sandboxed workspace)
   → Validation Engine        (allowlisted UNIT_TEST/STATIC_ANALYSIS/API_CONTRACT/BUILD/SECURITY/PERFORMANCE checks)
   → Final Report             (aggregated summary, exportable)
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full component breakdown, data flow, and security boundaries.

## 5. Technology Stack

Only what is actually present and used — nothing aspirational listed as current:

| Layer | Technology | Status |
|---|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic v2 | Implemented |
| Frontend | React 19, TypeScript, Vite 8 | Implemented |
| Frontend testing | Vitest, React Testing Library | Implemented (Phase 11) |
| Backend testing | pytest, ruff | Implemented |
| Database (dev/test) | SQLite (zero-dependency default) | Implemented, actually used |
| Database (production target) | PostgreSQL | **Proposed, never deployed or tested against** — `DATABASE_URL` switches the SQLAlchemy dialect with no code change, but this has not been exercised |
| Cache | Redis | **Not implemented** — deferred without a traffic number to justify it (ADR-003); `docker-compose.yml` defines it behind an opt-in profile, unwired |
| AI provider | Anthropic (`anthropic` SDK), behind a provider-agnostic `AIProvider` interface | Implemented; **no live API key is configured in this environment** — see §8 |
| Containerization | Docker (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`) | Present; **not built or run in this environment** (no Docker installed here) — NOT VALIDATED |
| API contract | OpenAPI (FastAPI auto-generated, structurally validated by the `API_CONTRACT` validation type) | Implemented |

## 6. Mandatory Use Case

> **Build a scalable URL shortener service with APIs, persistence, and analytics.**

Implemented at `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`, `GET /api/v1/urls/{short_code}/analytics/advanced` — see [docs/api-design-url-shortener.md](docs/api-design-url-shortener.md). **Built through the workbench, not alongside it**: its own requirement was registered and analyzed via the Requirement Analyzer, decomposed via the Task Decomposer, and routed through AI-assist → engineer review → artifact generation → artifact review → real validation — see `backend/tests/test_url_shortener_workbench_flow.py` and [docs/REQUIREMENT_TRACEABILITY.md](docs/REQUIREMENT_TRACEABILITY.md) for the real, captured chain of IDs proving it, not a description of what it should do.

Key decisions: CSPRNG Base62 short codes with DB-enforced collision retry ([ADR-002](docs/adr/ADR-002-short-code-strategy.md)); no cache yet, a documented decision tied to an unresolved traffic-volume ambiguity, not an oversight ([ADR-003](docs/adr/ADR-003-cache-strategy.md)); minimal analytics by default, extended only on explicit engineer choice ([ADR-004](docs/adr/ADR-004-analytics-design.md), [ADR-005](docs/adr/ADR-005-advanced-analytics-privacy.md)).

## 7. Demonstration Scenarios

* **Greenfield** — the URL shortener above, built from nothing. See [docs/scenarios/greenfield.md](docs/scenarios/greenfield.md).
* **Brownfield** — the existing URL shortener had slow redirects; improved without changing its public API, including a real regression (a lost-update race) found and fixed, not glossed over. See [docs/scenarios/brownfield.md](docs/scenarios/brownfield.md).
* **Ambiguous** — `"Improve the analytics."` was correctly blocked by the ambiguity gate until an engineer chose one of three presented interpretations. See [docs/scenarios/ambiguous.md](docs/scenarios/ambiguous.md).

All three are also demonstrable live in the UI's **Scenarios** screen.

## 8. AI Provider Configuration — Read This First

**No live AI provider is configured anywhere in this development environment** (no `AI_API_KEY`). Every "AI" response referenced throughout this project's tests, demos, and documentation is produced by `FakeAIProvider` (`backend/tests/support/fake_ai_provider.py`) returning **engineer-authored** content standing in for a real provider call — this is disclosed consistently, not hidden. `AnthropicProvider` (`backend/app/ai/anthropic_provider.py`) is fully implemented against the real Anthropic Messages API and used automatically once `AI_PROVIDER=anthropic` and `AI_API_KEY` are set (see `.env.example`), but it has **never been exercised against the live API in this environment** — this is an explicit, standing `NOT VALIDATED` item, not a gap that's been quietly assumed away.

## 9. Setup Guide

### Prerequisites

* Python 3.12 (any 3.10+ should work — the codebase uses `str | None` union syntax)
* Node.js 22+ / npm
* No PostgreSQL, Redis, or Docker required to run locally — see §5

### Environment Variables

Copy `.env.example` to `.env` and fill in only what you need:

```bash
cp .env.example .env
```

| Variable | Required? | Purpose |
|---|---|---|
| `DATABASE_URL` | No | Defaults to a local SQLite file. Accepts a `postgres://`, `postgresql://`, or `postgresql+psycopg://` URL for Postgres — the first two are normalized to the installed psycopg3 driver automatically (`app/core/database.py`), so a managed provider's connection string (e.g. Render's) works unmodified. |
| `REDIS_URL` | No | Unused — no code path reads it yet. |
| `CORS_ORIGINS` | No | Comma-separated allowed frontend origins. Defaults to the local Vite dev server; set explicitly for any deployed frontend origin. |
| `AI_PROVIDER` / `AI_API_KEY` / `AI_MODEL` | Only for `/analyze` and AI-assist endpoints | Without these, those endpoints return a clean `503`, not a silent failure. |
| `VITE_API_BASE_URL` | No | Frontend's backend URL; defaults to `http://localhost:8000`. |
| `IP_HASH_SALT` | No | Salts the URL-shortener's IP hash for repeat-visitor detection (ADR-005); a random salt is generated per process start if unset. |

**Never commit a real `.env`** — it's git-ignored; `.env.example` holds only empty placeholders.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Starts with no external services. `GET /health` → `{"status": "ok"}`. OpenAPI docs at `/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173).

### Database

SQLite by default — a local file created automatically on startup, no setup needed. PostgreSQL is the proposed production target (see §5) but has not been deployed or tested in this environment; there is no migration framework yet (`Base.metadata.create_all()` at startup — a deliberate deferral while the schema is still small, not an oversight).

### Redis

Not used by any code path. `docker-compose.yml` defines it behind an opt-in `with-db` profile for future use.

### Docker / Docker Compose

`docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` exist and describe the intended container setup (`docker compose up` for backend+frontend; `docker compose --profile with-db up` to add Postgres/Redis, unwired). **NOT VALIDATED** — Docker is not installed in this development environment, so these have never actually been built or run here.

### Deploying to Render

`render.yaml` at the repo root defines a Blueprint: the backend as a Docker web service (using `backend/Dockerfile`), the frontend as a static site, and a managed PostgreSQL database — this is the first deployment target where Postgres is actually exercised rather than just proposed (see §5).

1. In the Render dashboard: **New → Blueprint**, connect this GitHub repo. Render reads `render.yaml` and proposes `workbench-db` (Postgres), `workbench-backend` (Docker web service), and `workbench-frontend` (static site).
2. Before applying, note the exact names Render assigns each service (normally `workbench-backend`/`workbench-frontend` unless already taken) — the blueprint cross-references them (`CORS_ORIGINS` on the backend, `VITE_API_BASE_URL` on the frontend) assuming those exact names. If Render appends a suffix because the name is taken, update both env vars after the first deploy to match the real `.onrender.com` URLs, then redeploy.
3. `AI_API_KEY` is deliberately **not** in `render.yaml` (`sync: false`) — set it manually on the backend service under **Environment**, using a workspace-scoped key (see §8 above for why an identity-linked "Personal" key won't work).
4. `DATABASE_URL` is wired automatically from `workbench-db`'s connection string.

**Known, disclosed limitations of this path — NOT VALIDATED in this environment:**
* The Postgres code path (`_normalize_database_url` in `app/core/database.py`, and every query in the app) has never been run against a real Postgres instance here — only SQLite. This is the first time it would be exercised for real.
* Render's exact current free-tier terms (database retention, instance spin-down behavior) were not verified live — check the dashboard at deploy time rather than trusting a remembered price/limit.
* No CI/CD, staging environment, or rollback strategy beyond Render's own deploy history is set up.

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
├── README.md, ARCHITECTURE.md, AI_USAGE.md, CONTRIBUTING.md
├── .env.example, docker-compose.yml
│
├── backend/            # FastAPI app — see backend/README.md
│   ├── app/            # models, schemas, services, repositories, api/routes, ai/
│   └── tests/          # pytest suite (174 tests as of Phase 12)
│
├── frontend/           # React + TypeScript app
│   └── src/
│       ├── screens/    # Dashboard, Requirement, Plan, Tasks, AI Runs, Artifacts, Validation, Scenarios, Final Report
│       ├── hooks/       # useProjectData, workflowStage
│       ├── api/         # typed fetch clients
│       └── components/  # AppShell + shared pieces
│
├── generated/          # Sandboxed workspace for AI-generated artifacts (never written to outside this)
│
└── docs/
    ├── adr/             # Architecture Decision Records (ADR-001..006)
    ├── scenarios/       # greenfield.md, brownfield.md, ambiguous.md
    ├── validation/       # per-phase security reviews, performance evidence, validation strategy
    ├── security.md, performance.md            # Phase 12 consolidated review
    ├── FINAL_ENGINEERING_REPORT.md            # Phase 13
    ├── REQUIREMENT_TRACEABILITY.md            # Phase 13
    └── DEMO_GUIDE.md                          # Phase 13
```

## 11. AI-Assisted Development

AI is used task-by-task, never as a whole-system generator. Every meaningful AI interaction — what was asked, what came back, what the engineer found wrong, how it was corrected, how it was validated — is logged in [AI_USAGE.md](AI_USAGE.md), including the mistakes, not just the successes.

## 12. Validation

Nothing is claimed as tested unless it was actually executed. `NOT VALIDATED` is used literally, throughout every phase's documentation, whenever something wasn't run — see [docs/FINAL_ENGINEERING_REPORT.md](docs/FINAL_ENGINEERING_REPORT.md) for the consolidated list.

## 13. Git Workflow

Development proceeds through small, phase-scoped commits. Work is reviewed and validated before a commit is suggested; commits are never made automatically — see [CONTRIBUTING.md](CONTRIBUTING.md).

## 14. Current Status

**Phases 1–12 complete.** Phases 1–10 built the workbench and the URL shortener (greenfield, brownfield, and ambiguous scenarios). Phase 11 built the end-to-end UI (9 screens, `AppShell`, Vitest/RTL test suite). Phase 12 performed a security review (14 areas — see [docs/security.md](docs/security.md)) and a performance review including a genuine concurrent-load test that closed a previously `NOT VALIDATED` gap (see [docs/performance.md](docs/performance.md)). Phase 13 (this documentation pass) and Phase 14 (final end-to-end validation) close out the project — see [docs/FINAL_ENGINEERING_REPORT.md](docs/FINAL_ENGINEERING_REPORT.md) for the full account, including what remains `NOT VALIDATED`.
