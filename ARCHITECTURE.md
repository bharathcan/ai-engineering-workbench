# Architecture

> **Status: Proposed.** No implementation exists yet. This document describes the intended architecture direction for the AI Engineering Workbench and will be revised as implementation phases proceed.

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
* **Requirement Analyzer** — interprets an incoming requirement and produces a structured understanding of what is being asked.
* **Ambiguity Detector** — examines a requirement for underspecified or multi-interpretation elements and surfaces them to the engineer before task decomposition proceeds.
* **Task Planner** — breaks a requirement down into discrete, engineer-owned, AI-assistable tasks.
* **AI Assistance Layer** — a provider-abstracted layer through which individual tasks are sent to an AI model for assistance (e.g. code generation, debugging, refactoring suggestions).
* **Engineer Review** — the explicit human checkpoint where AI output is accepted, modified, or rejected before it becomes part of any artifact.
* **Artifact Generator** — produces the reviewed output as concrete artifacts: code, tests, and documentation.
* **Validation Engine** — checks generated artifacts against the originating requirement and records the outcome, including failures.
* **Persistence** — durable storage (proposed: PostgreSQL) for requirements, tasks, AI runs, engineer decisions, and artifacts, supporting traceability.
* **Generated project workspace** (`generated/`) — the on-disk location where artifacts produced by the workbench are written, separate from the workbench's own source.

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
