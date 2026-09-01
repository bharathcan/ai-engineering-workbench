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
├── backend/            # Backend service (not yet implemented)
├── frontend/           # Frontend application (not yet implemented)
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

## 13. Current Status

**Phase 1 — Repository Foundation**

The repository currently contains documentation and folder structure only. No application code, APIs, database models, or AI integrations have been implemented.
