# ADR-002: Short-Code Generation Strategy

## Status

Accepted — Phase 8D. Implemented in `backend/app/services/short_code.py` and `backend/app/repositories/url_repository.py`.

## Context

`POST /api/v1/urls` must produce a short code identifying the stored URL (URL-FR-001). The requirement analysis's ambiguity register (`docs/REQUIREMENTS.md` AMB-001) already flags that expected traffic volume is unresolved — this decision has to be sound at unknown, possibly-low-to-moderate scale without assuming a specific number that was never given.

## Decision

**Generate a random 7-character Base62 string per code, using a cryptographically secure RNG (`secrets.choice`), and rely on the database's own unique constraint — not a pre-check — to detect collisions, retrying with a fresh code up to 5 times on conflict.**

## Alternatives Considered

### Option A — Sequential/database-generated IDs (Base62-encoded auto-increment)

Encode the row's own auto-increment primary key as Base62 (`1` → `"1"`, `62` → `"10"`, etc.).

**Pros:** No collisions are possible by construction — trivially simple. **Cons:** Codes are sequential and predictable — anyone can enumerate `/1`, `/2`, `/3`, ... and discover every shortened URL in the system, including ones never meant to be shared. This is a real, immediate privacy/security problem for a public-facing shortener, not a hypothetical one.

### Option B — UUID-based codes

Use a UUID4 (or a shortened encoding of one) as the code.

**Pros:** Effectively collision-free without any retry logic; no coordination needed. **Cons:** A full UUID is far longer than a typical short URL wants to be (defeats the point of "short"); even a truncated/base62-encoded UUID prefix reintroduces a non-trivial collision probability without the benefit of Option C's simplicity, and doesn't naturally support tuning code length against expected volume.

### Option C — Random Base62 string with DB-enforced collision retry (chosen)

**Pros:** Short (7 chars → 62⁷ ≈ 3.5 trillion possibilities — collision probability is negligible at any traffic volume this system is likely to see without a resolved AMB-001), not enumerable (unlike Option A), and the retry logic is simple: attempt an insert, catch the unique-constraint violation, try a new random code. Using the database's real unique constraint as the source of truth (rather than a `SELECT` pre-check) also avoids a check-then-insert race condition under concurrent creation — see "Concurrency" below. **Cons:** Requires a retry loop (bounded, `MAX_COLLISION_RETRIES = 5`) and a way to signal exhaustion (`ShortCodeGenerationExhaustedError` → `503`) if every attempt collides, which in practice would only happen if the keyspace were nearly saturated — a scale problem, not a design flaw at today's traffic level.

## Recommendation

**Option C.** Option A is rejected outright on enumerability grounds — this is a security property, not a preference. Option B's length trade-off provides no advantage over Option C's collision math while working against the product's own "short" requirement. Option C is the standard, well-understood approach for this exact problem and keeps the implementation proportionate to a system whose real expected scale is still an open ambiguity (AMB-001).

## Consequences

* Every `POST /api/v1/urls` call may perform more than one insert attempt on a collision (rare, bounded at 5).
* `short_code` must remain a unique-indexed column — this is load-bearing for correctness, not just performance.
* Code length (7) is a tunable constant if real traffic data later suggests a longer code is warranted.

## Trade-offs

* **Simplicity vs. determinism** — a sequential ID is simpler to reason about and never collides, but is rejected here because its simplicity comes at the cost of enumerability.
* **Retry loop vs. guaranteed-unique generation** — accepting a bounded retry loop in exchange for short, non-enumerable codes, rather than guaranteeing uniqueness up front (which Option A does, at the cost above).

## Risks

* At very high insert rates with a much smaller code length, collision frequency would rise — not a concern at 7 characters for any volume this system is likely to see, but worth revisiting if the code length is ever shortened for aesthetic reasons.
* `ShortCodeGenerationExhaustedError` (503) is a real, reachable failure mode if the keyspace saturates — currently untested at the "actually exhaust 62⁷ codes" scale (that would take an impractically long test run); the retry-and-eventually-raise *logic itself* is tested directly by forcing a real collision and a real exhaustion via `backend/tests/test_url_repository.py`.

## Validation

`backend/tests/test_url_repository.py` and `backend/tests/test_short_code.py` actually exercise this: a forced real collision (two calls using overlapping code sequences) followed by a successful retry, exhausted-retries raising the correct exception, and 50 sequential real creations all receiving unique codes. **Not validated:** behavior under genuinely concurrent (multi-threaded/multi-process) simultaneous creation — the tests above are sequential; the correctness argument for concurrency (relying on the DB's own atomic unique-constraint check rather than a check-then-insert race) is a design argument, not something exercised under real concurrent load in this environment. ⚠ **ENGINEERING REVIEW REQUIRED** on that specific point before treating it as production-verified.
