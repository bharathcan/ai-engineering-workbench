# ADR-001: Human-in-the-Loop AI-Assisted Engineering

## Status

Proposed — Phase 1B. Not yet implemented.

## Context

The workbench must decide how AI participates in producing engineering artifacts (code, API contracts, schemas, tests, documentation) from a submitted requirement. The mandatory demonstration use case — a URL shortener with APIs, persistence, and analytics (see [REQUIREMENTS.md](../REQUIREMENTS.md)) — is well-defined enough to be fully automatable in principle, but the project's stated core principle is:

> AI assists the engineer within tasks; the engineer owns execution and quality.

This decision record exists to make explicit *why* that principle was chosen over the available alternatives, rather than leaving it as an unexamined default.

## Decision

**Use human-in-the-loop AI-assisted engineering rather than autonomous software generation.**

Concretely: AI operates within individually scoped, engineer-defined tasks (per [ENGINEERING_WORKFLOW.md](../ENGINEERING_WORKFLOW.md) Task Lifecycle and AI Run Lifecycle). Every AI run terminates in an explicit engineer decision (ACCEPT / MODIFY / REJECT) before its output becomes an artifact, and every artifact is validated — with `NOT_VALIDATED` as a first-class, non-default-to-pass state — before the engineer gives final acceptance.

## Alternatives Considered

### Option A — One-shot LLM application generation

A single prompt (e.g. the mandatory requirement sentence) is given to an LLM, which generates the entire application — backend, frontend, schema, tests — in one pass, with the engineer reviewing only the final result.

**Trade-offs:** Fast to produce a first version, and genuinely useful for prototyping or throwaway scaffolding. However, review happens only at the end, over a large, undifferentiated output — this makes it hard to trace any specific decision (e.g. "why this schema field," "why this endpoint shape") back to a specific reviewed choice, and hard to catch a wrong assumption before it has propagated through the entire generated system. It also does not naturally surface ambiguity: a one-shot generator tends to silently resolve an underspecified requirement (like "analytics" or "scalable") into *some* concrete choice rather than asking. This is not a claim that Option A produces bad code — only that it does not fit a workflow built around traceable, per-decision engineer ownership.

### Option B — Autonomous multi-agent software development

Multiple AI agents plan, implement, test, and iterate on the system with minimal human involvement, potentially including agents that review each other's work.

**Trade-offs:** Can handle more of the end-to-end workflow without engineer time, and multi-agent review can catch some classes of error automatically. However, it still concentrates ownership in the AI system rather than the engineer — "engineer review" becomes optional or advisory rather than a required gate, and validation performed entirely by agents raises the same integrity question the project explicitly guards against elsewhere: representing something as validated when no human has actually confirmed it (see [CONTRIBUTING.md](../CONTRIBUTING.md) Validation Integrity, and NFR-008). This is not a claim that Option B is unsafe in general — for well-bounded, low-stakes tasks it can work well — only that it conflicts with this project's core principle that the engineer owns execution and quality.

### Option C — Human-in-the-loop task-level AI assistance

AI assists within individually scoped tasks; every AI output requires an explicit engineer decision before becoming an artifact; every artifact requires actual validation before acceptance. This is the model already described in [README.md](../README.md), [ARCHITECTURE.md](../ARCHITECTURE.md), and [ENGINEERING_WORKFLOW.md](../ENGINEERING_WORKFLOW.md).

**Trade-offs:** Slower than Option A or B for producing a first working version, since it depends on engineer review time at each task boundary. It also demands more upfront structure (task decomposition, traceability IDs, explicit states) than either alternative. In exchange, it keeps every decision attributable to a specific reviewed task, keeps ambiguity visible instead of silently resolved, and keeps validation honest by construction (an artifact cannot become `DONE` without passing through `VALIDATION_REQUIRED`).

## Recommendation

**Option C is recommended and adopted.**

The project's demonstration goal is not merely to produce a working URL shortener — a one-shot or autonomous approach could likely do that — but to demonstrate requirement understanding, ambiguity detection, engineer-led task decomposition, AI assistance, and validation as a *reviewable process*. Options A and B optimize for output speed at the cost of making that process opaque or optional. Option C is the only one of the three that makes engineer ownership a structural property of the workflow rather than a matter of discipline, which directly matches the project's core principle and its non-functional requirements around auditability (NFR-004) and validation integrity (NFR-008).

## Consequences

* Every task requires an explicit engineer review step; the workbench cannot produce a "finished" artifact without one.
* The AI Assistance Layer must be scoped to operate on individual tasks, not the whole requirement at once (see [ARCHITECTURE.md](../ARCHITECTURE.md) AI Assistance Layer).
* The data model must support the full traceability chain (Requirement → Task → AI Run → Engineer Decision → Artifact → Test → Validation), which is more structure than a one-shot generator would need.
* Throughput is bounded by engineer review capacity, not just AI generation speed.

## Trade-offs

* **Speed vs. traceability** — Option C is deliberately slower than Options A/B in exchange for every artifact being attributable to a specific reviewed task and decision.
* **Structure vs. simplicity** — the task/AI-run/decision/artifact/validation data model is more upfront design than a simpler one-shot pipeline would require.
* **Engineer burden** — this model asks more of the engineer's time and attention than an autonomous approach; it trades convenience for control.

## Risks

* **Review fatigue** — if tasks are decomposed too finely, the volume of required engineer reviews could become burdensome enough that reviews become perfunctory, undermining the whole point of the gate. (Task decomposition granularity is not yet defined — this is a risk to watch during implementation, not one resolved here.)
* **False sense of rigor** — having a `VALIDATION_REQUIRED` state does not by itself guarantee validation is meaningful; a shallow or rubber-stamp validation step would satisfy the state machine without satisfying its intent.
* **Process overhead without corresponding payoff** — for very small or low-risk tasks, the full lifecycle (task → AI run → review → artifact → validation → acceptance) may be disproportionate to the task's actual risk. This ADR does not define a lightweight path for such cases.

## Validation

This decision has not been validated against a running implementation — none exists yet (Phase 1B is documentation only). It is currently a reasoned design choice, consistent with existing project documentation, and is subject to revision once the task/AI-run lifecycle is actually implemented and exercised against the URL shortener use case.
