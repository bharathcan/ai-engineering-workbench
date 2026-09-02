# Demo Guide

A practical walkthrough for demonstrating the workbench live. Assumes both servers are running locally (see [README.md](../README.md) §9) — backend on `:8000`, frontend on `:5173`. No AI provider is configured in this environment, so every AI response the demo shows is `FakeAIProvider`'s engineer-authored stand-in — say so up front rather than letting it look like a live model call.

## Setup (before the audience arrives)

```bash
# Terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --port 8000

# Terminal 2
cd frontend && npm run dev
```

Open `http://localhost:5173`. The top status bar should read **Status: Connected**.

## Suggested Flow

1. **Create a project** — go to the **Requirement** screen, paste the mandatory requirement text: *"Build a scalable URL shortener service with APIs, persistence, and analytics."* Click **Create Requirement**. Point out this becomes the selected project in the top selector immediately.

2. **Analyze the requirement** — click **Analyze Requirement**. Explain this is a real backend call to the Requirement Analyzer, returning a `FakeAIProvider` stand-in response (say this explicitly).

3. **Review ambiguities** — scroll to the Ambiguities section. Point out the distinct visual treatment for AI-suggested content vs. engineer-approved content — nothing here is auto-accepted just by being displayed.

4. **Generate the engineering plan** — go to **Engineering Plan**, click **Generate Engineering Plan**. Four tasks appear (short-code generation, persistence + redirect, click analytics, advanced analytics), each with acceptance criteria and requirement traceability. If this requirement had a `HIGH`-impact ambiguity, this step would instead show **PLAN BLOCKED** — demonstrate that live in step 13 instead of here, since this requirement's ambiguity isn't blocking.

5. **Review tasks** — go to **Tasks**, select the first task, walk through description/acceptance criteria/Definition of Done, then click **Accept**. Explain that Modify/Reject require a rationale — the API rejects a `MODIFY`/`REJECT` without one (422).

6. **Run AI assistance** — with the task accepted, use the AI Assistance panel to request `CODE_GENERATION`. Explain: this is the "AI Run" step — go to the **AI Runs** screen afterward to show the full record (prompt, response, provider/model, status).

7. **Review the AI recommendation** — back on the task, review the recommendation content, then **Accept** it. Point out the explicit statement that AI output is an engineering input, not automatically trusted code.

8. **Accept/Modify/Reject** — this is the moment to explicitly narrate: nothing before this point wrote any code. This decision is what allows generation to happen next.

9. **Generate artifacts** — trigger artifact generation for the accepted AI run. Go to the **Artifacts** screen, show the generated file's path, type, and version, and open the source viewer.

10. **Run validation** — on the **Validation** screen, run `STATIC_ANALYSIS` and `API_CONTRACT` against the artifact. Show the real command and real output/evidence — this is an actual `ruff check`/OpenAPI structural check running, not a canned response.

11. **Show validation evidence** — deliberately show one `NOT_VALIDATED` example too if available (e.g. the `PERFORMANCE` validation type at the generic artifact level returns `NOT_VALIDATED` by design) — this is the moment to make the PASSED-vs-NOT_VALIDATED distinction concrete, not just claimed.

12. **Show the greenfield URL shortener** — go to **Scenarios → Greenfield**. Explain this is the same requirement from steps 1–11, already fully built through this exact pipeline in earlier phases — reference [docs/scenarios/greenfield.md](scenarios/greenfield.md) and the real IDs in [docs/REQUIREMENT_TRACEABILITY.md](REQUIREMENT_TRACEABILITY.md).

13. **Show the brownfield scenario** — **Scenarios → Brownfield**. Walk through the real before/after performance numbers and — this is the strongest moment in the whole demo — the genuine regression that was found and fixed (a lost-update race from deferring the click-count write), not hidden. Mention Phase 12's concurrent-load re-verification.

14. **Show the ambiguous scenario** — **Scenarios → Ambiguous**. Click **Submit "Improve the analytics." and observe the live gate**. Watch it come back `BLOCKED — ENGINEER INPUT REQUIRED` live, in front of the audience — not a screenshot. Show the three interpretations and that none is pre-selected.

15. **Show the final engineering report** — go to **Final Report**. Walk through the aggregated decisions, artifacts, validation summary (explicitly call out the passed/failed/NOT_VALIDATED counts), risks, and assumptions. Click **Export as Markdown** to show the save/export capability.

16. **Close with honesty, not polish** — the strongest closing point is not "everything passed." It's: here's what's verified, here's what's explicitly `NOT VALIDATED` (no live AI provider, no PostgreSQL deployment, no authentication, no rate limiting — see [docs/security.md](security.md) and [docs/FINAL_ENGINEERING_REPORT.md](FINAL_ENGINEERING_REPORT.md)), and here's the reasoning behind every trade-off, not a hidden one.

## If Something Goes Wrong Live

* **Backend not running / `503` on analyze** — check `AI_PROVIDER`/`AI_API_KEY` aren't accidentally set to something invalid; requirement creation and listing work with zero config, only `/analyze` and AI-assist need them.
* **CORS error in the browser console** — frontend must run on `localhost:5173` exactly; `app/main.py`'s CORS allowlist is hardcoded to that origin (see [docs/security.md](security.md) Remaining Risks).
* **Plan generation returns BLOCKED unexpectedly** — this is not a bug to hide; narrate it as the ambiguity gate working, exactly as demonstrated intentionally in step 14.
