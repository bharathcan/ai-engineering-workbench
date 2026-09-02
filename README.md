# AI Engineering Workbench

> AI-assisted software engineering workbench that transforms software requirements into structured, production-ready, and validated engineering artifacts with human-in-the-loop review.

---

## 1. Project Overview

The **AI Engineering Workbench** is a system for demonstrating how AI can be integrated responsibly into a real software engineering workflow. Rather than treating AI as a one-shot code generator, the workbench treats it as an assistant that operates *within* individual engineering tasks — requirement analysis, code generation, testing, debugging, refactoring — while the engineer remains responsible for reviewing, validating, and accepting every output before it becomes part of the system.

The workbench is being built incrementally, in reviewed phases, starting with repository foundation and documentation before any implementation work begins.

## 2. Problem Statement

Software teams are increasingly using AI tools to accelerate development, but this often happens in an unstructured, unauditable way: prompts are ad hoc, outputs are accepted without review, and there is no record of what the AI got wrong or how the engineer corrected it.

The objective of this project is to demonstrate how AI can assist engineers in transforming software requirements into production-quality engineering outcomes — with a workflow that makes requirement understanding, ambiguity detection, task decomposition, AI assistance, engineer review, and validation all explicit and traceable.

## 3. Core Principle

> **AI assists the engineer within tasks; the engineer owns execution and quality.**

AI is a participant in individual tasks, not the owner of the engineering process. Every AI-assisted output passes through engineer review before it is accepted into the codebase.

## 4. Engineering Workflow

```text
Requirement
     ↓
Requirement Understanding
     ↓
Ambiguity Detection
     ↓
Task Decomposition
     ↓
AI-Assisted Engineering
     ↓
Engineer Review
     ↓
Code / APIs / Schema / Tests / Documentation
     ↓
Validation
     ↓
Risks & Trade-offs
     ↓
Final Engineering Summary
```

## 5. Core Capabilities

The workbench is intended to demonstrate the following capabilities:

* **Requirement analysis** — interpreting a stated requirement and identifying what it actually asks for.
* **Ambiguity detection** — identifying underspecified or multi-interpretation requirements before implementation begins.
* **Task decomposition** — breaking a requirement into engineer-owned, AI-assistable tasks.
* **AI assistance** — using AI within a task (code generation, debugging, refactoring, test writing) rather than as a single end-to-end generator.
* **Engineer review** — every AI output is explicitly reviewed and accepted, modified, or rejected.
* **Artifact generation** — producing code, API contracts, schemas, tests, and documentation as reviewed artifacts.
* **Validation** — checking that generated artifacts actually satisfy the requirement before acceptance.
* **Risk analysis** — identifying security, performance, and reliability risks in generated work.
* **Engineering summary** — a final, honest account of what was built, what was assumed, and what remains uncertain.

## 6. Mandatory Use Case

The mandatory assignment use case for this workbench is:

> **Build a scalable URL shortener service with APIs, persistence, and analytics.**

This use case is documented here as a requirement only. **It has not been implemented yet.** Implementation will proceed through the engineering workflow described above, in later phases.

## 7. Demonstration Scenarios

The workbench is intended to demonstrate three categories of engineering scenario:

### Greenfield

Building a new system from scratch, with no pre-existing code or constraints. This is the primary mode for the URL shortener use case.

### Brownfield

Enhancing, refactoring, or fixing an existing system, where the engineer must work within existing code, constraints, and conventions rather than starting fresh.

### Ambiguous

A deliberately underspecified requirement:

> **Improve the analytics.**

For the ambiguous scenario, the system must explicitly identify the ambiguity and present multiple plausible interpretations to the engineer **before** any implementation is attempted. Implementation must not proceed on an ambiguous requirement without first surfacing that ambiguity.

## 8. Technology Direction

The following technologies are the **proposed** direction for this project. None of them are implemented yet — they describe intent, not current state.

```text
Frontend      React + TypeScript
Backend       Python + FastAPI
Database      PostgreSQL
Cache         Redis
Testing       Pytest
API Contract  OpenAPI
Container     Docker
AI            Provider abstraction
```

## 9. Repository Structure

```text
ai-engineering-workbench/
├── README.md
├── AI_USAGE.md
├── ARCHITECTURE.md
├── CONTRIBUTING.md
├── .gitignore
├── .env.example
│
├── backend/            # FastAPI application skeleton (health check only; see backend/README.md)
├── frontend/           # React + TypeScript application shell (see Local Development)
├── generated/          # Generated project workspace / artifacts
├── tests/              # Test suites
├── scripts/            # Developer/automation scripts
│
├── docs/
│   ├── adr/            # Architecture Decision Records
│   ├── scenarios/      # Greenfield / brownfield / ambiguous scenario write-ups
│   └── validation/     # Validation reports and evidence
│
└── examples/
    ├── greenfield/     # Greenfield scenario walkthroughs
    ├── brownfield/     # Brownfield scenario walkthroughs
    └── ambiguous/      # Ambiguous scenario walkthroughs
```

## 10. AI-Assisted Development

AI is used **task-by-task**, not as a one-shot generator of the entire system. Each unit of work — a function, an endpoint, a schema, a test suite — is scoped, given to the AI with context, reviewed by the engineer, and only then integrated. This keeps AI contributions small enough to review meaningfully and traceable back to the task and requirement that motivated them.

## 11. Validation

AI-generated outputs are not treated as correct by default. Every artifact — code, tests, documentation — must be validated against the originating requirement before it is accepted. Validation results (including failures) are recorded honestly; nothing is fabricated. See [AI_USAGE.md](AI_USAGE.md) for the audit trail structure used to record this.

## 12. Git Workflow

Development proceeds through small, meaningful, incremental commits tied to specific phases of work. At the end of each meaningful phase, work is reviewed, validated, and documented, and a commit is suggested — but not made automatically. See [CONTRIBUTING.md](CONTRIBUTING.md) for the full phase-gate process.

## 13. Local Development

This section documents only what is actually implemented so far: a runnable application skeleton with a single `/health` endpoint and a frontend shell that displays backend connectivity. It does not include requirement analysis, task decomposition, AI integration, or the URL shortener — those are not implemented yet.

### Backend

```bash
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Runs with no environment variables set and no external services (PostgreSQL, Redis) running — none are required yet. See [backend/README.md](backend/README.md) for details.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Opens at [http://localhost:5173](http://localhost:5173). Set `VITE_API_BASE_URL` (see [.env.example](.env.example)) if the backend isn't running at the default `http://localhost:8000`.

### Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

### Health Check

`GET /health` on the backend returns `{"status": "ok"}` with HTTP 200. It requires no authentication and no external services. The frontend shell calls this endpoint on load and displays `Connected`, `Checking backend…`, or `Backend unavailable` depending on the result.

### Requirement Analyzer

The frontend now includes a Requirement Analyzer form (textarea + "Analyze Requirement") below the health status. It calls `POST /api/v1/requirements`, then `POST /api/v1/requirements/{id}/analyze`, and displays the structured result — summary, functional/non-functional requirements, ambiguities, assumptions, constraints, success criteria, and engineering concerns, with ambiguities and assumptions visually distinguished. See [docs/api-design.md](docs/api-design.md) for the full API contract.

Analysis requires a configured AI provider (`AI_PROVIDER=anthropic` and `AI_API_KEY` in `.env` — see [.env.example](.env.example)); without one, `/analyze` returns a clean `503` rather than failing silently. Requirement creation and retrieval work with no AI provider configured.

### Task Decomposition

After a requirement is analyzed, the frontend shows a "Generate Engineering Plan" button. It calls `POST /api/v1/requirements/{id}/tasks` and displays either the resulting plan — each task's title, description, requirement traceability, dependencies, acceptance criteria, and expected AI-assistance type, with inline Accept / Modify / Reject controls (`POST /api/v1/tasks/{task_id}/decision`) — or, if the analysis has an unresolved `HIGH`-impact ambiguity, a **"PLAN BLOCKED"** message naming the ambiguity that must be clarified first. See [docs/api-design.md](docs/api-design.md) for the full endpoint set and the ambiguity-gate rule.

### AI-Assisted Task Execution

Once a task is `APPROVED` (accepted in plan review), its card shows an **AI Assistance** section: pick an assistance type (`CODE_GENERATION`, `DEBUGGING`, etc.), optionally add instructions, and "Request AI Assistance" (`POST /api/v1/tasks/{id}/ai-assist`). The resulting recommendation — summary, approach, files, tests, risks, confidence — is displayed with an **⚠ ENGINEERING REVIEW REQUIRED** banner whenever confidence isn't `HIGH`, and Accept / Modify / Reject controls (`POST /api/v1/ai-runs/{ai_run_id}/decision`). Choosing Modify opens a "What should be changed?" box; the next AI request for that task is automatically linked to the one it's revising (`AI-RUN-001 → MODIFY → AI-RUN-002`, both kept — never overwritten). A task's full AI Run History is listed on its card.

### Artifact Generation

Once an AI run's recommendation has been `ACCEPT`ed, its card shows a **"Generate Artifacts"** button (`POST /api/v1/ai-runs/{ai_run_id}/artifacts`) — a rejected or still-pending recommendation never shows this option, since generation is only reachable after `ACCEPT`. Each resulting artifact — real proposed file content, not just a description — is shown as a card (type, path, version, status) with a Show Diff/Content toggle and Accept/Reject controls (`POST /api/v1/artifacts/{artifact_id}/decision`). Regenerating creates a new version that supersedes the prior one — both are kept, visible via `GET /api/v1/tasks/{id}/artifacts`. **Every write is contained to the sandboxed `generated/` workspace** — an unsafe path (absolute, `..`, or anything resolving outside it) is rejected before anything is written; see [docs/api-design.md](docs/api-design.md) "Controlled File Writes".

### Validation Engine

Once an artifact is `APPROVED`, its card shows a **Validation** dashboard: seven checks (Unit Tests, Integration, API Contract, Static Analysis, Security, Performance, Build) as clickable pills — ✓ passed, ✗ failed, ⚠ not validated, ○ not yet run. Clicking one runs it for real (`POST /api/v1/artifacts/{id}/validate`) and expands to show the actual command and evidence (e.g. the real `pytest`/`ruff` output tail). The API only ever accepts a `validation_type` from a fixed set — never a raw command — see [docs/validation/validation-strategy.md](docs/validation/validation-strategy.md) for exactly what each type runs and its documented limits.

## 14. URL Shortener (Mandatory Use Case)

The mandatory assignment requirement — "Build a scalable URL shortener service with APIs, persistence, and analytics." — is implemented at `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`. See [docs/api-design-url-shortener.md](docs/api-design-url-shortener.md) for its own API contract, distinct from the workbench's own meta-API above.

**Built through the workbench, not alongside it**: its requirement was registered and analyzed via the Requirement Analyzer, decomposed into tasks via the Task Decomposer, and its create-URL task was routed through AI-assist → engineer review → artifact generation → artifact review → real validation — the same pipeline documented in sections 11–13 above, exercised on this feature specifically. `backend/tests/test_url_shortener_workbench_flow.py` is a permanent, re-runnable proof of that chain, not a one-time manual demo.

Key engineering decisions: random Base62 short codes with DB-enforced collision retry ([ADR-002](docs/adr/ADR-002-short-code-strategy.md)), no cache for now — a documented decision tied to the still-unresolved AMB-001 traffic ambiguity, not an oversight ([ADR-003](docs/adr/ADR-003-cache-strategy.md)), and minimal click-count + timestamp analytics — no per-click event log, no PII ([ADR-004](docs/adr/ADR-004-analytics-design.md)). Real (not invented) latency numbers are in [docs/validation/url-shortener-performance.md](docs/validation/url-shortener-performance.md); the security review (URL validation, SSRF-adjacent blocking, the open rate-limiting gap) is in [docs/validation/PHASE-8-SECURITY-REVIEW.md](docs/validation/PHASE-8-SECURITY-REVIEW.md).

## 16. Ambiguous Requirement — Engineer-Resolved (Phase 10)

> Improve the analytics.

Registered and analyzed through the real Requirement Analyzer, which correctly flagged this as materially ambiguous (`HIGH`-impact `AMB-001` — no analytics system or desired improvement is named). Attempting task decomposition on it was **actually blocked** — `plan.status == "BLOCKED"`, 0 tasks generated — not silently guessed. Three interpretations (Reporting / Real-Time / Advanced User Analytics) were presented with trade-offs; **the engineer chose Interpretation C**. Only then was it implemented: `GET /api/v1/urls/{short_code}/analytics/advanced` (device/browser/referrer breakdown, repeat-visitor detection), with hashed — never raw — IP storage and an honest `geographic_status` rather than fabricated location data, since choosing the more data-invasive interpretation directly reopened [ADR-004](docs/adr/ADR-004-analytics-design.md)'s privacy-by-minimalism reasoning. See [ADR-005](docs/adr/ADR-005-advanced-analytics-privacy.md).

## 15. Current Status

**Phase 10 — Ambiguous Requirement, Engineer-Resolved**

The workbench demonstrated refusing to guess: a materially ambiguous requirement was blocked by the Task Decomposer's own gate until an explicit engineer decision resolved it, then implemented with a fresh privacy review specific to that choice — not a rubber-stamped continuation of Phase 8's original analytics scope. See [AI_USAGE.md](AI_USAGE.md) TASK-008 for the full engineering summary. Phase 9's brownfield optimization (redirect performance, a real regression found and fixed) remains documented in [docs/scenarios/brownfield.md](docs/scenarios/brownfield.md) and [AI_USAGE.md](AI_USAGE.md) TASK-007.
