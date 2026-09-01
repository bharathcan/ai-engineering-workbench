# Engineering Workflow

> **Status: Draft — Phase 1B.** This document models the intended human + AI engineering lifecycle for the workbench. No part of this lifecycle is implemented yet — this is a specification, not a running state machine. See [REQUIREMENTS.md](REQUIREMENTS.md) for the requirements this workflow is designed to satisfy.

## 1. Lifecycle Overview

```text
Requirement
     ↓
Requirement Analysis
     ↓
Ambiguity Detection
     ↓
Engineer Review
     ↓
Requirement Accepted
     ↓
Task Decomposition
     ↓
Engineer Review
     ↓
Task Selected
     ↓
AI Assistance
     ↓
AI Output
     ↓
Engineer Review
     │
 ┌───┼──────────┐
 ▼   ▼          ▼
Accept Modify   Reject
 │
 ▼
Artifact
 │
 ▼
Validation
 │
 ├── PASS
 ├── FAIL → correction
 └── NOT VALIDATED
 │
 ▼
Engineer Acceptance
```

### State-by-state explanation

* **Requirement** — a raw requirement is submitted by the engineer (FR-001). Example: the mandatory URL shortener sentence.
* **Requirement Analysis** — the system extracts intent, functional requirements, and non-functional requirements from the raw text (FR-002).
* **Ambiguity Detection** — the system checks the analyzed requirement for missing or underspecified information and produces an ambiguity register entry for anything it finds (FR-003), rather than guessing.
* **Engineer Review** (of the analysis) — the engineer reviews the extracted requirements and any detected ambiguities. Ambiguities are resolved here explicitly, by the engineer, not silently by the system (FR-004).
* **Requirement Accepted** — the requirement (with ambiguities resolved or explicitly deferred) is considered ready for decomposition.
* **Task Decomposition** — the accepted requirement is broken into discrete engineering tasks with IDs, objectives, descriptions, dependencies, and acceptance criteria (FR-005).
* **Engineer Review** (of the task list) — the engineer reviews the proposed decomposition before any task is worked on.
* **Task Selected** — the engineer picks a specific task to work on next. Tasks are worked one at a time, not all at once, per the "AI assists within tasks" principle.
* **AI Assistance** — AI is invoked to assist with the selected task (FR-006). This is scoped to the one task, not the whole requirement.
* **AI Output** — the AI's raw output for the task, preserved as produced (see [AI_USAGE.md](../AI_USAGE.md) rule: preserve incorrect AI first attempts).
* **Engineer Review** (of the AI output) — the engineer evaluates the AI's output and makes one of three decisions (FR-007):
  * **Accept** — used as-is.
  * **Modify** — the engineer corrects the output; the correction is recorded.
  * **Reject** — the output is discarded; the reason is recorded. A rejected task returns to **AI Assistance** (retry) or is re-scoped at **Task Decomposition**.
* **Artifact** — an Accepted or Modified output becomes a tracked artifact: code, an API contract, a schema, a test, or documentation (FR-008).
* **Validation** — the artifact is checked against the task's acceptance criteria and the originating requirement (FR-009). Validation is not optional and not assumed — see Validation States below.
  * **PASS** — the artifact satisfies its acceptance criteria.
  * **FAIL** — the artifact does not satisfy its acceptance criteria; this routes to a correction cycle (back to AI Assistance or direct engineer correction).
  * **NOT VALIDATED** — validation has not yet been performed. This is a distinct, first-class outcome — it is never treated as equivalent to PASS (NFR-008).
* **Engineer Acceptance** — the engineer gives final sign-off on the validated artifact, closing the task.

This lifecycle repeats per task until all tasks for a requirement are complete, at which point an Engineering Summary is produced (FR-012).

---

## 2. Task Lifecycle

```text
PLANNED
   ↓
READY
   ↓
IN_PROGRESS
   ↓
AI_REVIEW_REQUIRED
   ↓
ENGINEER_REVIEW
   ↓
VALIDATION_REQUIRED
   ↓
VALIDATED
   ↓
DONE
```

Additional states that can be entered from multiple points in the lifecycle above:

```text
REJECTED
BLOCKED
VALIDATION_FAILED
```

### Transitions

* **PLANNED → READY** — the task has been decomposed and has no unresolved dependencies; the engineer has reviewed the decomposition.
* **READY → IN_PROGRESS** — the engineer selects the task and AI assistance begins (or the engineer begins working it directly).
* **IN_PROGRESS → AI_REVIEW_REQUIRED** — an AI run has produced output for the task that needs engineer review.
* **AI_REVIEW_REQUIRED → ENGINEER_REVIEW** — the engineer begins evaluating the AI output.
* **ENGINEER_REVIEW → VALIDATION_REQUIRED** — the engineer has Accepted or Modified the output into an artifact; it now needs validation.
* **ENGINEER_REVIEW → REJECTED** — the engineer rejects the AI output entirely. From `REJECTED`, the task returns to `IN_PROGRESS` (retry with AI) or `PLANNED` (re-scope) at the engineer's discretion.
* **VALIDATION_REQUIRED → VALIDATED** — validation was actually performed and passed.
* **VALIDATION_REQUIRED → VALIDATION_FAILED** — validation was actually performed and failed. From here, the task returns to `IN_PROGRESS` for correction.
* **VALIDATED → DONE** — the engineer gives final acceptance (Engineer Acceptance in the lifecycle above).
* **Any state → BLOCKED** — the task cannot proceed due to an unresolved dependency, an unresolved ambiguity, or an external constraint. `BLOCKED` returns to its prior state once the blocker is resolved.

A task must never move from `AI_REVIEW_REQUIRED` directly to `DONE` — engineer review and validation are mandatory intermediate states, not optional shortcuts.

---

## 3. AI Run Lifecycle

```text
AI_REQUESTED
     ↓
AI_COMPLETED
     ↓
ENGINEER_REVIEW
     ↓
ACCEPTED
     OR
MODIFICATION_REQUESTED
     OR
REJECTED
```

* **AI_REQUESTED** — a task-scoped prompt has been sent to the AI Assistance Layer.
* **AI_COMPLETED** — the AI has returned output (or failed — see NFR-005; a failed run is recorded as failed, not silently retried into a false completion).
* **ENGINEER_REVIEW** — the engineer evaluates the completed AI run.
* **ACCEPTED / MODIFICATION_REQUESTED / REJECTED** — the terminal engineer decision for this specific AI run, matching FR-007.

**AI output must never transition directly to production acceptance.** Every AI run terminates in an explicit engineer decision; there is no path from `AI_COMPLETED` directly to an artifact being marked final.

---

## 4. Validation States

```text
NOT_VALIDATED
PASS
FAIL
```

* **NOT_VALIDATED** — the default state of any artifact until validation is actually performed. This is a first-class state, not the absence of a state.
* **PASS** — validation was actually performed and the artifact met its acceptance criteria.
* **FAIL** — validation was actually performed and the artifact did not meet its acceptance criteria.

**Missing validation is never treated as PASS.** An artifact with no validation record is `NOT_VALIDATED`, and must be reported as such (per [CONTRIBUTING.md](../CONTRIBUTING.md) Validation Integrity rules and NFR-008) — it is never implied to have passed simply because no failure was recorded.

---

## 5. Traceability Model

```text
REQ-001
   │
   ├── TASK-001
   │      │
   │      ├── AI-RUN-001
   │      │       ↓
   │      │   DECISION-001
   │      │
   │      └── ARTIFACT-001
   │                │
   │                ├── TEST-001
   │                └── VALIDATION-001
   │
   └── RISK-001
```

Each ID type connects to the others as follows:

* A **Requirement** (`REQ-*`) decomposes into one or more **Tasks** (`TASK-*`) and may surface one or more **Risks** (`RISK-*`).
* A **Task** may involve one or more **AI Runs** (`AI-RUN-*`), each of which resolves to exactly one **Engineer Decision** (`DECISION-*`).
* An accepted or modified AI run (or direct engineer work) produces an **Artifact** (`ARTIFACT-*`).
* An artifact is checked by one or more **Tests** (`TEST-*`) and has a **Validation** record (`VALIDATION-*`) reflecting the outcome of those checks.

### Why this matters

This model exists so that every piece of the final system — every line of code, every schema, every test — can be traced backward to the specific requirement that justified it, the specific AI run (if any) that produced it, and the specific engineer decision that accepted it. This is what makes engineering ownership real rather than nominal: if an artifact exists, there is a recorded chain showing *why* it exists, *who* (or what) produced it, and *who* decided to keep it. It is also what makes the [AI_USAGE.md](../AI_USAGE.md) audit trail auditable in practice rather than just in principle — an entry there should be traceable to a concrete `TASK-*` / `AI-RUN-*` / `ARTIFACT-*` chain, not a free-floating note.
