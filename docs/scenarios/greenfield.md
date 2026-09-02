# Greenfield Scenario — URL Shortener Built From Scratch

The mandatory assignment requirement, built from a blank codebase, entirely through the workbench pipeline (not hand-written alongside it):

> Build a scalable URL shortener service with APIs, persistence, and analytics.

## How It Was Designed and Implemented

Processed through the exact same pipeline every other requirement in this project goes through — no shortcut, no hand-authored bypass:

1. **Requirement Analyzer** (`POST /api/v1/requirements`, then `.../analyze`) — produced functional requirements (`FR-001..003`: shorten a URL, redirect, track clicks), non-functional requirements (scale/latency expectations), and a `HIGH`-relevance-but-not-blocking ambiguity (`AMB-001`: expected traffic volume is never quantified in the requirement text).
2. **Task Decomposer** (`POST /api/v1/requirements/{id}/tasks`) — produced 4 tasks: short-code generation, URL persistence + redirect, click analytics, and (later, Phase 10) advanced analytics — each with requirement traceability, dependencies, acceptance criteria, and an expected AI-assistance category.
3. **Engineer review of the plan** — each task reviewed individually (`ACCEPT`/`MODIFY`/`REJECT`) before any AI-assist request could be made against it.
4. **AI-assisted execution** — each task's AI recommendation reviewed and accepted before artifact generation was reachable.
5. **Artifact generation** — real proposed file content written into the sandboxed `generated/` workspace, one artifact per implied file, versioned on regeneration.
6. **Validation** — `STATIC_ANALYSIS`, `API_CONTRACT`, `UNIT_TEST`, and other allowlisted checks run against generated artifacts.

`backend/tests/test_url_shortener_workbench_flow.py` is the permanent, re-runnable proof of this chain end-to-end. [docs/REQUIREMENT_TRACEABILITY.md](../REQUIREMENT_TRACEABILITY.md) captures one real, executed run's actual IDs (Requirement `REQ-001` → Task `TASK-001` → AI Run `AI-RUN-001` → Artifact `ARTIFACT-001` → Validations `VALIDATION-001`/`VALIDATION-002`, both `PASSED`) — not a description of what the chain should look like.

## Key Engineering Decisions

* **Short codes:** CSPRNG-generated Base62, 7 characters, with DB-enforced collision retry rather than a pre-check-then-insert (which has a race window under concurrent creation) — see [ADR-002](../adr/ADR-002-short-code-strategy.md).
* **No cache:** deliberately deferred, tied to the still-unresolved traffic-volume ambiguity (`AMB-001`) rather than added speculatively — see [ADR-003](../adr/ADR-003-cache-strategy.md).
* **Minimal analytics by default:** click-count + timestamp only, no per-click event log, no PII — until Phase 10's ambiguous-requirement scenario resulted in an explicit engineer choice to add more (see [ambiguous.md](ambiguous.md)) — see [ADR-004](../adr/ADR-004-analytics-design.md).
* **Redirect status code `307`, not `301`/`308`:** deliberately non-permanent so browsers don't cache the redirect and stop hitting this server, which would silently undercount clicks.

## API Surface

`POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`, `GET /api/v1/urls/{short_code}/analytics/advanced` — full contract in [docs/api-design-url-shortener.md](../api-design-url-shortener.md).

## Security

Scheme allowlist (`http`/`https` only), private/internal-IP blocking via Python's `ipaddress` module, `localhost`-by-name blocking, URL length cap, CSPRNG short codes (not enumerable). Reviewed fresh in Phase 12 — see [docs/security.md](../security.md) §5, §8, §9.

## Performance

Real, measured — not estimated — via `backend/app/services/performance_probe.py` against a live `uvicorn` instance. Baseline (Phase 8) and post-optimization (Phase 9) numbers in [docs/validation/url-shortener-performance.md](../validation/url-shortener-performance.md); a fresh sequential re-measurement plus a first-ever concurrent-load test in [docs/performance.md](../performance.md) (Phase 12) — 300 concurrent requests, 0 lost clicks.

## Limitations — NOT VALIDATED

* PostgreSQL behavior — only SQLite has been exercised.
* Redis-backed caching — not implemented (see ADR-003).
* Production-scale traffic (thousands of req/s, sustained load, multi-worker deployment).
* No authentication or rate limiting exists on any endpoint (see [docs/security.md](../security.md) Remaining Risks) — acceptable for this prototype's scope, not fixed.
