# Ambiguous Scenario — "Improve the analytics."

## Why This Cannot Be Safely Implemented Without Clarification

> Improve the analytics.

This sentence names no target, no metric, and no scope. "Improve" could mean: make existing reports easier to read, add real-time visibility, or collect richer data about visitors. Each of those is a materially different engineering task — different data model, different privacy posture, different infrastructure. Picking one silently would mean the AI (or the engineer, guessing on the AI's behalf) invented requirements that were never actually given. This project's global rule is explicit: **no silent assumptions** — an ambiguity must be identified, not resolved by guessing.

## What Actually Happened (Not a Description of What Should Happen)

Registered and analyzed through the real Requirement Analyzer, exactly as any other requirement:

1. `POST /api/v1/requirements` with the exact, unmodified text `"Improve the analytics."`
2. `POST .../analyze` — the analyzer correctly flagged this as a `HIGH`-impact ambiguity (`AMB-001`: no analytics system or desired improvement is named).
3. `POST .../tasks` — the Task Decomposer's ambiguity gate **actually fired**: response was `status: "BLOCKED"`, **0 tasks generated**. This is the real mechanism, verified by making the actual request and reading the actual response — not an assertion about intended behavior.

## Interpretations Presented — Not Chosen By AI

| | Interpretation | Scope | Trade-off |
|---|---|---|---|
| A | Reporting Analytics | Scheduled/aggregate reports — daily/weekly click summaries, top links | Low complexity, low privacy risk; not real-time, no per-visitor insight |
| B | Real-Time Analytics | Live dashboards / streaming click counts | Immediate visibility; more infrastructure, still no behavioral insight |
| C | Advanced User Analytics | Device, browser, referrer, geographic, repeat-visitor tracking per click | Richest insight; **"additional data collection, privacy/security implications, increased complexity"** (the option's own stated con) |

All three were presented with trade-offs, none pre-selected. **The engineer explicitly chose Interpretation C.**

## Implementation — Only After the Explicit Decision

Choosing C directly reopened [ADR-004](../adr/ADR-004-analytics-design.md)'s minimal-data-collection reasoning — that reasoning was correct for the scope it addressed, but the engineer had now explicitly asked for more. Rather than treat "the engineer chose the more invasive option" as license to be careless, the implementation applied privacy mitigations regardless of the broader scope chosen (documented in [ADR-005](../adr/ADR-005-advanced-analytics-privacy.md)):

* **Hashed, never raw, IP** — salted SHA-256, used only for repeat-visitor equality checks, not reversible to the original address.
* **Honest, not fabricated, geography** — no GeoIP data source exists in this environment; the response says so explicitly (`geographic_status`) rather than inventing a location.
* **User-Agent classified into coarse categories only** — the raw string is stored (needed for classification) but never returned in any analytics response.

Result: `GET /api/v1/urls/{short_code}/analytics/advanced` — device/browser/referrer breakdown, repeat-visitor rate. `backend/tests/test_advanced_analytics_workbench_flow.py` proves the *clarified* requirement's ambiguity is now `LOW`-impact and no longer blocks planning, in contrast to the original.

## The UI Never Auto-Implements This

The Scenarios screen's Ambiguous tab lets an engineer submit `"Improve the analytics."` fresh and watch the gate fire live (a new requirement each time, not a replay of the one above) — it shows the `BLOCKED — ENGINEER INPUT REQUIRED` status and the three interpretations, and does nothing further until the engineer acts. If a submission is ever *not* blocked, the UI treats that as a finding to investigate, not a success (see `frontend/src/screens/ScenariosScreen.test.tsx`, which tests exactly this case).

## NOT VALIDATED

* Any legal/compliance review of the Interpretation-C data collection (explicitly flagged as required before real deployment in ADR-005).
* The device/browser classifier's accuracy against a broad, real-world sample of User-Agent strings (only a handful of common ones are tested; the module discloses itself as a heuristic, not a maintained database).
* Whether a differently-worded ambiguous requirement (not this exact sentence) would also be caught — the analyzer's ambiguity detection is AI-generated per-requirement, not a fixed rule list, so this is not something a single test proves in general.
