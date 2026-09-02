# Contributing

This document defines the development rules for this repository. It applies to all contributors, human or AI-assisted, and governs how work is phased, reviewed, and committed.

## Phase Gates

Work proceeds in phases. After each meaningful phase, the following steps are required, in order:

1. **Review** — the work produced in the phase is reviewed against what was actually asked for.
2. **Validate** — the work is checked/tested as applicable; no validation is claimed that was not actually performed.
3. **Document** — relevant documentation (README, ARCHITECTURE, AI_USAGE, etc.) is updated to reflect what was actually built.
4. **Suggest Git commit** — a commit message is proposed for the phase's work.
5. **STOP**

Work does **not** continue into the next phase automatically. The next phase begins only when the repository owner explicitly says:

**continue**

## No Silent Assumptions

When a requirement is underspecified or ambiguous, the following categories must be kept explicitly distinct — never blurred together silently:

* **Requirements** — what was actually, explicitly asked for.
* **Assumptions** — gaps filled in without explicit confirmation, stated as such.
* **Interpretations** — one reading among several plausible readings of an ambiguous requirement.
* **Engineering decisions** — choices made by the engineer, with reasoning, where the requirement allowed more than one valid approach.

Any of these that is not a direct requirement must be labeled as what it is when presented.

## AI Review

All AI-generated output must be reviewed by the engineer before it is accepted into the project. Every review results in one of three explicit decisions:

* **ACCEPT** — the output is correct and used as-is.
* **MODIFY** — the output is used after engineer correction; the correction is recorded.
* **REJECT** — the output is discarded; the reason is recorded.

See [AI_USAGE.md](AI_USAGE.md) for how these decisions are logged.

## Validation Integrity

The following must never be fabricated, implied, or overstated:

* Tests (their existence, or their results)
* Coverage (numbers must reflect what was actually measured)
* Security review results
* Performance results
* Build results

If something was not actually run or checked, that must be stated plainly rather than omitted or implied otherwise.

## Git Discipline

* Commits are small and meaningful, scoped to a coherent unit of work.
* Commit messages describe what changed and, where relevant, why.
* Commits are not created automatically — they are proposed at each phase gate and made only on explicit approval.
