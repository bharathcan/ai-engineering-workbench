# ADR-006: Defer `starlette`/`fastapi` Security-Advisory Upgrade

## Status

Accepted — Phase 12 (Security & Performance Hardening).

## Context

Phase 12's security review ran `pip-audit` against the backend's actual installed dependencies (not asserted — see `docs/security.md` §14) and found 10 known advisories, all against two packages: `starlette` (0.41.3, 7 distinct issues) and `pytest` (8.3.4, 1 issue).

`fastapi==0.115.6` pins `starlette<0.42.0,>=0.40.0`. Every advisory's fix version is `starlette>=1.0.0` — there is no patched `starlette` release compatible with the currently pinned FastAPI version. Fixing these advisories directly requires also upgrading FastAPI itself, from `0.115.6` to something recent enough to accept a `1.x` `starlette` (the latest available is `0.141.1` — many releases ahead).

Applicability review (full detail in `docs/security.md` §14) found that 9 of the 10 advisories require code patterns this codebase does not use: reading `request.url`/`request.url.path`/`request.url.hostname` for a security-sensitive decision (this codebase's only use of `request.url` is a log message), serving files via `StaticFiles`/`FileResponse` (not used anywhere), or class-based `HTTPEndpoint` routes without an explicit `methods=` (not used — all routes are function-based `@router.get`/`@router.post`). The 10th (`pytest`'s local-tmp-dir advisory) is a dev-only-tooling, local-attacker-only issue.

## Decision

**Do not upgrade `starlette`/`fastapi`/`pytest` in this phase.** Document the advisories, their real (checked, not assumed) applicability, and the upgrade path as a deferred follow-up task.

## Alternatives Considered

### Option A — Upgrade `starlette` in place, pinning around FastAPI's range

**Rejected:** not possible — no `starlette` version satisfies both "patched" and FastAPI 0.115.6's pin simultaneously. This isn't a trade-off, it's a hard incompatibility.

### Option B — Upgrade FastAPI (and therefore `starlette`) together, now

**Rejected for this phase, not rejected permanently.** A FastAPI major-version-adjacent jump (0.115 → 0.141+) is a real, cross-cutting change: it touches every route file, every response model, and potentially the AI provider integration's dependency graph. This phase's time budget does not include a full regression pass across the entire backend after a change of that size. Performing it anyway, under time pressure, would trade a **currently-inapplicable, theoretical** vulnerability for a **real, unverified** risk of breaking the application — the wrong trade for a project whose stated priority is honest validation over the appearance of completeness.

### Option C — Defer, with the applicability review and upgrade path documented (chosen)

Ship the review findings honestly: which advisories exist, which are actually reachable given this codebase's real usage (verified by reading the code, not assumed), and record the upgrade as a concrete, scoped follow-up: *upgrade `fastapi` and `starlette` together, then run the full test suite before accepting the change* — not bundled into a hardening pass that doesn't have room to validate it properly.

## Consequences

* The 10 advisories remain present in the installed dependency tree. None are currently exploitable given this codebase's actual usage (verified, not assumed) — see `docs/security.md` §14 for the per-advisory reasoning.
* Any future change that starts reading `request.url` for a security decision, serves static files, or adds a class-based `HTTPEndpoint` route would need this ADR re-opened — the "not applicable" conclusion is conditional on the code staying the way it is, not a permanent exemption.
* The dependency upgrade remains an open, tracked item (`docs/security.md`, Remaining Risks #3) rather than something silently dropped once this phase ends.
