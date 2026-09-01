# AI Usage Audit

This file records meaningful AI-assisted engineering work performed in this repository. Its purpose is to make AI involvement in the codebase **traceable and honest**: what was asked of the AI, what it produced, what was wrong with that output, how the engineer corrected it, and what was ultimately decided.

This is an audit trail, not a changelog. It exists so that anyone reviewing this project can see exactly where AI contributed, where it was wrong, and how the engineer exercised judgment.

## Entry Structure

Every future AI usage entry must follow this structure:

```text
Task
↓
Objective
↓
Prompt
↓
AI First Attempt
↓
Engineer Review
↓
Issues Found
↓
Correction
↓
Validation
↓
Final Decision
```

Each field, explained:

* **Task** — the specific, scoped unit of engineering work.
* **Objective** — what the task was meant to achieve.
* **Prompt** — what was actually given to the AI (context included).
* **AI First Attempt** — the AI's output, preserved as-is, including mistakes.
* **Engineer Review** — the engineer's assessment of that output.
* **Issues Found** — concrete problems identified, if any.
* **Correction** — what the engineer changed, and why.
* **Validation** — how the corrected output was actually verified (tests run, checks performed). If nothing was actually validated, this must say so.
* **Final Decision** — ACCEPT / MODIFY / REJECT, with brief reasoning.

## Rules

1. **Preserve incorrect AI first attempts.** Do not delete or clean up a flawed first attempt — record it as it was produced.
2. **Do not rewrite AI history.** Entries are not edited after the fact to look better in hindsight.
3. **Record engineer decisions.** Every entry states what the engineer decided and why.
4. **Record corrections.** If the engineer changed the AI's output, the change and its reasoning are documented.
5. **Never claim validation that was not actually performed.** If tests weren't run, say tests weren't run. If coverage wasn't measured, say so.
6. **Explicitly flag uncertainty.** If the engineer or the AI is not confident about something, that uncertainty is recorded, not hidden.
7. **AI-generated output is not automatically accepted.** Every entry ends in an explicit ACCEPT, MODIFY, or REJECT decision.

## Log

_No implementation-level (code/API/schema/test) AI-assisted tasks have been completed yet._

### Entry 001 — Formalize Requirements and Engineering Workflow

* **Task** — Formalize requirements and engineering workflow (Phase 1B — Requirements & Engineering Specification).
* **Objective** — Convert the mandatory assignment sentence and existing repository documentation into a precise, traceable engineering specification (`REQUIREMENTS.md`, `ENGINEERING_WORKFLOW.md`, `ADR-001`) before any implementation begins.
* **Prompt** — Engineer instructions to inspect existing repository documentation (README, ARCHITECTURE, AI_USAGE, CONTRIBUTING) for consistency, then produce a formal requirements specification distinguishing workbench requirements from URL shortener requirements, an ambiguity register, an engineering workflow document defining task/AI-run/validation lifecycles and a traceability model, and an ADR on human-in-the-loop vs. autonomous AI architecture — documentation only, no application code.
* **AI Assistance** — Requirements structuring (FR/NFR/URL-FR/URL-NFR IDs), ambiguity identification (Ambiguity Register), workflow modeling (task lifecycle, AI run lifecycle, validation states, traceability model), and ADR drafting (options analysis and recommendation).
* **AI First Attempt** — `docs/REQUIREMENTS.md`, `docs/ENGINEERING_WORKFLOW.md`, and `docs/adr/ADR-001-human-in-the-loop-architecture.md`, produced as committed to the repository at this entry's timestamp.
* **Engineer Review** — PENDING.
* **Issues Found** — Not yet assessed; pending engineer review.
* **Correction** — Not yet assessed; pending engineer review.
* **Validation** — Only structural documentation checks have been performed (file existence, requirement ID uniqueness, cross-document terminology consistency, no accidental implementation code). No review of the requirements' or ADR's actual engineering judgment has occurred yet — that is the engineer review this entry is pending.
* **Final Decision** — **PENDING ENGINEER REVIEW.**

This repository is currently in **Phase 1B — Requirements & Engineering Specification**. No code, API, schema, or test generation has occurred. Further entries will be added as AI-assisted engineering tasks are performed in later phases.
