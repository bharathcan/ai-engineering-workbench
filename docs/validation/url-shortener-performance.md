# URL Shortener Performance — Phase 8K

Real measurements, taken against a live `uvicorn` instance of this actual codebase using `backend/app/services/performance_probe.py`. No numbers here are invented or estimated — every figure below came from an actual run, reproducible via that module.

## Environment (read this before the numbers)

* **SQLite**, not PostgreSQL — the zero-dependency local default (see `ARCHITECTURE.md` Persistence). PostgreSQL is the proposed production database; these numbers do **not** represent Postgres behavior, which has different lock/concurrency/durability characteristics.
* **Sequential requests**, not concurrent — the probe issues one request at a time and waits for the response before sending the next. This measures per-request latency accurately; it does **not** measure throughput under concurrent load, connection-pool contention, or lock contention between simultaneous writers.
* **Loopback (`127.0.0.1`)**, single process, single worker, on a developer laptop — no real network latency, no load balancer, no multiple replicas.
* **No Redis / cache** — this is intentionally measuring the uncached path, since ADR-003 decided against adding a cache without a traffic number to justify it. These numbers are the actual input to that decision, not a hypothetical.

**These results are indicative of this code path's own overhead in this environment only — not a production capacity claim.**

## Method

`backend/app/services/performance_probe.py::probe_post` / `probe_get` sends real HTTP requests via `httpx.Client` against a locally running `uvicorn app.main:app` instance, timing each with `time.perf_counter()`. Percentiles use the nearest-rank method over all captured per-request latencies.

## Results

### `POST /api/v1/urls` (create)

| Metric | Value |
|---|---|
| Requests | 300 |
| Success rate | 100% (0 errors) |
| p50 | 0.99 ms |
| p95 | 1.13 ms |
| p99 | 1.44 ms |
| Throughput | 960.0 req/s |
| Wall time | 0.31 s |

### `GET /{short_code}` (redirect)

| Metric | Value |
|---|---|
| Requests | 500 |
| Success rate | 100% (0 errors, all `307`) |
| p50 | 0.98 ms |
| p95 | 1.14 ms |
| p99 | 1.29 ms |
| Throughput | 1004.1 req/s |
| Wall time | 0.50 s |

### Analytics accuracy under load

`click_count` after the 500-request redirect probe: **500** — exactly matching the 500 successful redirects, with zero drift. This confirms `record_click` (ADR-004) tracks accurately under this sequential load; it does **not** confirm accuracy under concurrent writes to the same row (see Known Limitations).

A smaller earlier run (50 create / 100 redirect) produced consistent p50/p95 figures (~1ms) with a higher p99 (12.13ms) on the create path — likely first-write SQLite file overhead (page cache warm-up / initial fsync), not reproduced in the larger run above. Both runs are reported rather than only the more favorable one.

## Interpretation

Both endpoints resolve in roughly ~1ms server-side latency at this scale, in this environment — the ADR-002 indexed short-code lookup and the ADR-003 no-cache decision both look reasonable against this baseline: the DB query itself is not currently a meaningful bottleneck. This is the concrete evidence ADR-003 defers to, not an assumption.

## Known limitations — NOT VALIDATED

* **Concurrent/parallel load** — not measured. No multi-threaded or multi-process load-generation harness was used; all requests above are strictly sequential. Real concurrent-write behavior (especially SQLite's single-writer characteristics) is unverified.
* **PostgreSQL performance** — not measured; no Postgres instance is running in this environment (see `ARCHITECTURE.md`).
* **Sustained/soak load** — only short bursts (300–500 requests) were run; no measurement of behavior over sustained high load or of connection/resource exhaustion over time.
* **Network-realistic latency** — loopback only; no real network hop, TLS handshake, or load balancer in the path.

⚠ **ENGINEERING REVIEW REQUIRED** before treating any of the above as production capacity guidance — these numbers answer "is the uncached code path itself slow," and the answer at this scale is no; they do not answer "how does this scale under real concurrent production traffic."
