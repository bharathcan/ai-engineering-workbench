# Brownfield Scenario — Redirect Performance

Phase 9's required demonstration: AI-assisted engineering against an *existing* implementation (the Phase 8 URL shortener), not a greenfield build.

## Original system

The Phase 8 URL shortener (`backend/app/api/routes/urls.py`, `backend/app/services/url_service.py`, `backend/app/repositories/url_repository.py`) — see [ARCHITECTURE.md](../../ARCHITECTURE.md) and [docs/api-design-url-shortener.md](../api-design-url-shortener.md).

## Requirement

> The existing URL shortener has slow redirect performance. Improve performance without changing the public API.

Processed through the same Requirement Analyzer / Task Decomposer / task-review / AI-assist pipeline as Phase 8 — see `backend/tests/test_brownfield_performance_flow.py` for the durable, re-runnable proof. As in every prior phase, no live AI provider is configured in this environment; the analysis/recommendation content is engineer-authored, standing in for a provider response.

The Requirement Analyzer flagged, correctly, that **"slow" is never quantified** — no baseline number or target is given (`AMB-001` in this scenario's analysis). This didn't block the work (unlike Phase 10's material ambiguity), but it meant the first real step had to be establishing an actual number, not assuming one.

## Baseline

Measured for real via `backend/app/services/performance_probe.py` against a live `uvicorn` instance, before any code change, 500 sequential `GET /{short_code}` requests:

| Metric | Before |
|---|---|
| p50 | 0.981 ms |
| p95 | 1.185 ms |
| p99 | 1.475 ms |
| Throughput | 990.4 req/s |
| Success rate | 100% |

## Bottleneck — identified from the code, not assumed

Per the workbench's own instruction not to automatically assume Redis is the answer: the code was read before anything was changed. `resolve_and_record_click` (the pre-Phase-9 implementation) did two **sequential, synchronous** database round-trips before returning a response:

1. `get_by_short_code` — a `SELECT` to resolve the code.
2. `record_click` — a separate `UPDATE` + `COMMIT` to increment the click count.

The second step is bookkeeping the client doesn't need to wait for — the redirect can be returned as soon as the `SELECT` resolves. This is a real, code-level cause, not a generic "add a cache" guess, and required no new infrastructure to fix.

## Engineer decision

**AI recommendation (AI-RUN-001):** defer the click-count write to a FastAPI `BackgroundTask`, so it runs after the response is already sent.

**Engineer review: MODIFY** — approach accepted, but required an explicit regression test pinning the exact response contract (status/headers/body) before treating "unchanged public API" as verified rather than assumed.

**AI-RUN-002 (revision, linked via `revised_from_ai_run_id`, AI-RUN-001 preserved unmodified):** same approach, with the regression test added. **ACCEPT**ed.

## Implementation

`app/services/url_service.py`: split `resolve_and_record_click` into `resolve_active_url` (read-only) and `record_click_for` (the write). `app/api/routes/urls.py`: the redirect route now calls `resolve_active_url`, builds the `RedirectResponse`, and schedules `record_click_for` via `BackgroundTasks.add_task` — which FastAPI runs after the response is sent, per its own documented dependency-with-yield/background-task ordering guarantee. **The response itself — `307`, `Location` header, empty body, `404`/`410` error cases — is byte-for-byte unchanged.**

## A real regression, found and fixed — not hidden

The first "after" measurement showed a genuine problem: **498 clicks recorded out of 500 successful redirects.** Deferring the write created a window where overlapping background tasks for the same row could both read the same starting `click_count` before either wrote back — a classic lost-update race that the *original* synchronous code never had (each request's write fully completed, in order, before the next began). This was **not anticipated in the plan** — it was caught by actually re-measuring, not assumed away.

**Root cause:** `record_click` incremented via Python-side read-modify-write (`url.click_count += 1`, then `UPDATE`) — the read and the write were two separate steps with a gap between them.

**Fix:** rewrote the increment as a single atomic SQL statement (`UPDATE ... SET click_count = click_count + 1 ...`), evaluated by the database against the row's current value at execution time, not a value read earlier in Python. This closes the race regardless of how many background tasks overlap.

A second, smaller issue surfaced while fixing the first: the corrected version originally still called `db.refresh(url)` afterward, which failed (`InvalidRequestError: Instance is not persistent within this Session`) when run as a background task. Not needed for correctness — nothing reads `url` again after the background task completes — so it was removed rather than worked around.

## Regression testing

The full pre-existing test suite (145 tests, unmodified) was run before and after the optimization — all passed both times, which is itself the regression proof for every other endpoint's behavior. One new test was added specifically for this change: `test_redirect_response_contract_unchanged_after_phase_9_optimization` (`backend/tests/test_urls_api.py`), pinning exact status code, `Location` header, empty body, and confirming the click still lands (asynchronously) by the time analytics is next checked.

## Performance comparison — real numbers, both runs

| Metric | Before | After (with race) | After (fixed) |
|---|---|---|---|
| p50 | 0.981 ms | 0.648 ms | 0.662 ms |
| p95 | 1.185 ms | 0.831 ms | 0.782 ms |
| p99 | 1.475 ms | 1.947 ms | 1.144 ms |
| Throughput | 990.4 req/s | 1432.2 req/s | 1421.7 req/s |
| Click accuracy | 500/500 | **498/500** | 500/500 |

The middle column is reported too, not discarded, because it's what real measurement actually showed before the fix — including a p99 regression (1.947ms, worse than baseline) that the atomic-increment fix also resolved as a side effect.

**Net result:** ~33% p50 improvement, ~34% p95 improvement, ~44% throughput improvement, with click-tracking accuracy fully preserved and the public API contract unchanged (verified by a dedicated test, not assumed).

## Limitations — NOT VALIDATED

* Same environment caveats as [url-shortener-performance.md](../validation/url-shortener-performance.md): SQLite (not Postgres), sequential (not concurrent) load generation, loopback only.
* The race condition was only ever observed at 500 sequential requests against SQLite in this environment — it is a real, general class of bug (read-modify-write vs. atomic update), not something whose *frequency* was characterized under other conditions.
* No test exists that specifically reproduces the race under genuine concurrent load (the same limitation noted in ADR-002) — the fix is verified by measurement (500/500 recorded) and by understanding the mechanism, not by a dedicated concurrency stress test.
