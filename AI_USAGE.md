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

_No implementation-level AI-assisted tasks have been completed yet._

This repository is currently in **Phase 1 — Repository Foundation**. No code, API, schema, or test generation has occurred. Entries will be added here as AI-assisted engineering tasks are performed in later phases.
