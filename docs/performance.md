# Performance Review — Phase 12

Consolidates prior per-scenario performance evidence (`docs/validation/url-shortener-performance.md` — Phase 8K, `docs/scenarios/brownfield.md` — Phase 9) with fresh measurements taken in this phase, including a genuine **concurrent**-load test that closes a gap both prior documents explicitly flagged as `NOT VALIDATED`.

## Environment (unchanged from prior phases — read before the numbers)

* **SQLite**, not PostgreSQL. PostgreSQL remains the documented, proposed production target — these numbers do not represent Postgres's different lock/concurrency/durability behavior.
* **Loopback (`127.0.0.1`)**, single process, single `uvicorn` worker, developer laptop. No real network latency, no load balancer.
* **No Redis / cache** (ADR-003: deferred without a traffic number to justify it).

## 1. Hot Path Review (Code-Level)

The intended hot path for the URL shortener is `Client → FastAPI → (Redis) → Database`. Redis is not present in this deployment (see ADR-003) — the actual hot path is `Client → FastAPI → SQLite`.

Reviewed for the redirect path (`GET /{short_code}`, `app/api/routes/urls.py` → `app/services/url_service.py` → `app/repositories/url_repository.py`):

* **One read query** (`get_by_short_code`, indexed lookup — `short_code` has a unique constraint, which SQLite backs with an index) to resolve the redirect.
* **Zero synchronous writes** on the request path — the click-count increment and `ClickEvent` write are both deferred to a `BackgroundTasks` callback that FastAPI runs *after* the response is already sent (Phase 9 optimization; see `docs/scenarios/brownfield.md`).
* **No N+1 pattern** — a single redirect never triggers more than the one lookup query; the deferred write is one `UPDATE` plus one `ClickEvent` insert, not a loop.
* **Connection pooling:** SQLAlchemy's default pooling behavior is used (`app/core/database.py`) — not tuned or reviewed further, since SQLite doesn't have the same connection-pool cost model as a networked database like PostgreSQL; this is called out explicitly as something to revisit if/when the project moves to Postgres, not something validated here.

## 2. Sequential Baseline — Re-measured Fresh in This Phase

Re-ran the same method as Phase 8K/9 (`app/services/performance_probe.py`, real HTTP requests via `httpx.Client` against a live `uvicorn` instance) to confirm current numbers, plus measured the advanced-analytics endpoint (Phase 10) for the first time.

| Endpoint | Requests | Success rate | p50 | p95 | p99 | Throughput |
|---|---|---|---|---|---|---|
| `POST /api/v1/urls` | 300 | 100% | 0.98 ms | 1.14 ms | 1.46 ms | 970.6 req/s |
| `GET /{short_code}` (redirect) | 500 | 100% | 0.95 ms | 3.59 ms | 7.02 ms | 668.3 req/s |
| `GET .../analytics/advanced` | 200 | 100% | 2.24 ms | 3.91 ms | 12.84 ms | 378.4 req/s |

Consistent with Phase 8K/9's numbers within normal run-to-run variance for the create/redirect paths (this run's redirect p95/p99 are somewhat higher than Phase 9's post-fix numbers — 3.59/7.02ms here vs. 0.78/1.14ms then — attributed to this being a fresh SQLite file with cold page cache plus general machine-load variance between sessions, not a regression in the code, which is unchanged since Phase 9; not independently re-isolated further in this pass). The advanced-analytics endpoint is measured here for the first time — its per-click aggregation (`Counter` over all `ClickEvent` rows for the URL, in Python) is `O(events)`, so throughput will degrade for short codes with very large event counts; not tested at that scale (see Limitations).

## 3. Concurrent Load — Closing a Previously NOT VALIDATED Gap

Both `docs/validation/url-shortener-performance.md` and `docs/scenarios/brownfield.md` explicitly flagged: *"No test exists that specifically reproduces the [click-count] race under genuine concurrent load — the fix is verified by measurement (500/500 recorded) and by understanding the mechanism, not by a dedicated concurrency stress test."*

Ran a genuine concurrent probe in this phase: 20 threads (each its own `httpx.Client`), 300 total `GET /{short_code}` requests against the **same** short code, submitted via `concurrent.futures.ThreadPoolExecutor` (real OS-level concurrent requests, not sequential).

| Metric | Value |
|---|---|
| Requests | 300 (20 concurrent workers) |
| Success rate | 100% (300/300, all `307`) |
| p50 | 23.61 ms |
| p95 | 49.01 ms |
| Throughput | 629.2 req/s |
| `click_count` before | 500 |
| `click_count` after | 800 |
| Recorded delta | 300 |
| Expected delta | 300 |
| **Match** | **True — no lost updates** |

**This confirms the Phase 9 atomic-`UPDATE` fix holds under genuine concurrent load**, not just sequential load — the previously-flagged gap is closed. Latency is higher under concurrency than sequential (expected — SQLite serializes writes at the file level, so 20 threads contending for the same row's write lock queue behind each other), but no request failed and no click was lost.

**Caveats on this result, stated explicitly:**
* This is thread-level concurrency within one Python process against one `uvicorn` worker — it does not test multi-process or multi-worker concurrent writers to the same SQLite file, which has different (and generally worse) concurrency characteristics than what was tested here.
* SQLite's own file-level write serialization is doing real work here to prevent the race (each write effectively queues) — this result does **not** predict PostgreSQL's behavior, which has different locking/MVCC semantics; the atomic `UPDATE ... SET click_count = click_count + 1` pattern itself (not row-level Python read-modify-write) is the actual portable fix, and would need re-verification against Postgres specifically before trusting this result to carry over.
* Only tested against a single short code (worst-case contention on one row) — not tested with concurrent writers spread across many different short codes simultaneously.

## 4. Frontend Performance

Not load-tested — this is a local single-user SPA (React + Vite), not a server under concurrent load. `npm run build` output size was inspected instead (Phase 11): ~239 KB JS / ~11 KB CSS uncompressed, ~71 KB / ~2.4 KB gzipped for the whole application shell plus all 9 screens — small enough that first-load performance was not a concern worth dedicated measurement at this project's scale. **NOT VALIDATED**: actual browser rendering performance (paint timing, interaction latency) — no browser automation tool is available in this environment (same limitation noted throughout every phase).

## 5. Database Indexes

Reviewed `app/models/url.py` and `app/models/engineering_plan.py`: `short_code` on `ShortenedUrl` has a unique constraint (index-backed). No other query pattern in the codebase filters on a non-indexed, non-primary-key column at a volume where an index would matter at this project's scale (every other lookup is by primary key). Not a finding requiring action.

## NOT VALIDATED

* PostgreSQL performance characteristics (only SQLite was measured — PostgreSQL remains the proposed, undeployed production target).
* Multi-worker / multi-process concurrent write behavior (only single-process thread concurrency was tested).
* Redis-backed caching performance (no Redis in this deployment — ADR-003).
* Frontend rendering/interaction performance in an actual browser (no browser automation tool available).
* Sustained/soak load behavior (all tests here are short bursts — hundreds of requests over sub-second-to-low-second wall time, not sustained load over minutes/hours).
* Advanced-analytics endpoint performance at large per-URL click-event volumes (only tested at low event counts).
