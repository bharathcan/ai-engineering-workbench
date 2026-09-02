# ADR-003: Cache Strategy for Redirects

## Status

Accepted — Phase 8H. No cache is implemented.

## Context

`GET /{short_code}` is the hottest path in a URL shortener — every redirect does a DB lookup by `short_code`. Redis was proposed in `ARCHITECTURE.md`'s technology direction from Phase 1B, and the assignment's "scalable" requirement is exactly the kind of thing a redirect cache is meant to address. This decision is about whether to actually implement it now.

## Decision

**Do not implement Redis (or any cache) for redirects in this phase.** The lookup remains a direct, indexed database query. This is revisited once the currently-unresolved ambiguity about expected traffic (`docs/REQUIREMENTS.md` AMB-001) is actually resolved with real numbers.

## Reasoning

Introducing a cache is only a win if the thing it's caching is actually a bottleneck. Right now:

* `short_code` is a unique, indexed column (ADR-002) — a lookup by it is an indexed point query, not a table scan. `docs/validation/url-shortener-performance.md` measures this directly against the actual running service.
* No real traffic volume has ever been specified for this system — AMB-001 is still open. Sizing a cache (TTL, eviction policy, memory budget) against an unknown load is guessing, not engineering.
* This dev environment has no Redis instance, and standing one up purely to "look scalable" without a load number to justify it is exactly the kind of premature infrastructure the workbench's own instructions warn against ("do not introduce Kafka/event streaming simply to appear scalable" — the same principle applies to Redis here).
* A cache adds real correctness surface area that has to be gotten right: cache-aside population, TTL choice, stale-data handling if a URL is later disabled, and invalidation — none of which are free, and all of which are wasted engineering effort if the DB lookup was never actually the bottleneck.

This is a **documented decision against building something now**, not an oversight — the alternative (implementing Redis) was genuinely evaluated, not skipped.

## Alternatives Considered

### Option A — Redis cache-aside (proposed, not implemented)

On a redirect: check Redis for `short_code` → `original_url`; on a miss, query the DB, populate Redis with a TTL, then redirect. On URL creation, either populate the cache eagerly or leave it to populate lazily on first hit.

**If this is implemented later**, the concrete plan is:
* **TTL:** a bounded TTL (e.g. minutes, not hours) rather than no expiry, so a disabled/expired URL doesn't serve a stale redirect indefinitely from cache.
* **Cache miss:** falls through to the real DB lookup — a cache miss must never be treated as "URL doesn't exist."
* **Cache failure (Redis down):** must fail open to the DB lookup, never fail the redirect — a cache is an optimization, not a dependency the redirect path should be hostage to.
* **Invalidation:** on manual disable (`status` → `DISABLED`), actively evict rather than waiting out the TTL, so disabling a URL takes effect immediately.

### Option B — In-process (application-memory) cache

An LRU cache inside the FastAPI process itself, no external service.

**Pros:** no new infrastructure at all. **Cons:** doesn't share state across multiple backend instances (each process/replica would have its own, inconsistent cache) — a real problem the moment this runs as more than one instance, which "scalable" implies it eventually will. Not chosen for the same reason as Option A: no traffic data justifies adding it yet, and it has a real correctness gap (multi-instance inconsistency) that Redis wouldn't.

### Option C — No cache (chosen)

Direct indexed DB query on every redirect, exactly as implemented.

## Recommendation

**Option C, now — Option A, later, once AMB-001 is resolved with real numbers.** This is a decision to defer, with a concrete plan already written down for when deferral ends, not a decision to never do it.

## Consequences

* Every redirect does one real DB query. Measured latency for this is in `docs/validation/url-shortener-performance.md` — the actual number this decision is trading against, not a guess.
* Revisiting this decision has a clear trigger: real traffic data resolving AMB-001, or the performance measurement showing the DB lookup is actually a bottleneck at realistic load — not a fixed timeline.

## Trade-offs

* **Simplicity now vs. headroom later** — no cache is simpler and has nothing to get wrong, at the cost of not having the scaling headroom Redis would add if traffic did materialize.

## Risks

* If traffic materializes suddenly without warning, redirect latency scales with DB load with no cache buffer in front of it — mitigated by the fact that the current measured baseline (see the performance doc) has headroom before this becomes a real problem, and by ADR-002's indexed-lookup design already being the cheap part of the request.

## Validation

The reasoning above rests on the actual measured redirect latency in `docs/validation/url-shortener-performance.md` (real numbers, this dev environment) — not on an assumption that the DB lookup is "probably fine." No cache was implemented, so there is nothing to validate about cache behavior itself; that section of Option A above is a documented plan, explicitly `NOT VALIDATED` because it doesn't exist yet.
