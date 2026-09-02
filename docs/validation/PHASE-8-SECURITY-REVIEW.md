# Phase 8 Security Review — URL Shortener

Reviewed before closing Phase 8. Scope: `POST /api/v1/urls`, `GET /{short_code}`, `GET /api/v1/urls/{short_code}/analytics`. Builds on the Phase 3–7 reviews for the workbench itself, which are unrelated to this feature's own surface.

## URL validation

`app/schemas/url.py::CreateUrlRequest` enforces: non-empty, ≤2048 chars, scheme must be `http`/`https` (rejects `javascript:`, `file:`, `data:`, `ftp:`, etc. — see `test_disallowed_scheme_is_rejected`), and a host must be present. **Status: addressed** — actually tested against real disallowed-scheme payloads, not just described.

## Malicious URLs / SSRF considerations

This service **stores and redirects** — it never fetches a submitted URL server-side (no preview/screenshot/HEAD-check feature exists), so the classic SSRF pattern (tricking *this server* into calling an internal endpoint) does not directly apply. What does apply: this service could be used to **obscure** a link into internal infrastructure behind an innocuous-looking short code, or to point at a cloud metadata endpoint (`169.254.169.254`) hoping a *downstream* client fetches it blindly. Mitigated: `CreateUrlRequest` rejects `localhost`, and any hostname that is a private/loopback/link-local/reserved IP literal (`ipaddress.ip_address(...).is_private/is_loopback/is_link_local/is_reserved`) — tested directly, including the metadata-endpoint case (`test_private_or_internal_ip_literal_is_rejected`).

**Not addressed, disclosed rather than silently gapped:** DNS-based bypass. A hostname like `internal.example.com` that *resolves* to a private IP at request time is not caught — the validator checks IP literals only, not DNS resolution at creation time (resolving DNS during request validation has its own cost/complexity/TOCTOU trade-offs that weren't judged worth taking on in this phase). ⚠ **ENGINEERING REVIEW REQUIRED** if this system will ever be exposed where an attacker controls DNS for a domain they'd submit.

## Rate limiting

**Not implemented.** There is no per-IP or per-key rate limit on `POST /api/v1/urls` or `GET /{short_code}`. This is a real, open gap, not a claimed protection — no in-memory or Redis-backed limiter exists in this codebase, and ADR-003 already decided against adding Redis infrastructure without a traffic justification. Without a rate limit, this endpoint is enumerable/abusable at whatever rate a caller wants to send. Documented here as unresolved, matching the instruction not to claim protection that isn't implemented.

## Input validation

Beyond the URL scheme/host checks above: `expires_at` is a standard Pydantic `datetime`, rejecting malformed values with a clean `422`. `short_code` in the redirect path is constrained by a path pattern (`^[0-9A-Za-z]{4,16}$`) — an arbitrary long or symbol-laden path segment doesn't reach the lookup logic at all, it 404s at the routing layer.

## Error leakage

All URL-shortener error responses follow the same project-wide pattern as every prior phase: `HTTPException` with a clean `detail` string, no stack trace or internal exception text, and the same global unhandled-exception safety net in `app/main.py`. Not specifically re-tested with a forced-failure test in this phase (the pattern itself was already tested for other resources in Phases 3–7); judged sufficient given it's the identical code path, not a new one.

## Analytics privacy

Per ADR-004, only `click_count` and `last_accessed_at` are stored — no IP address, user-agent, referrer, or any other per-visitor identifying data. This is a deliberate privacy-by-minimalism choice, not an oversight: nothing is collected that would need a retention/deletion policy for personal data, because no personal data is collected.

## Summary

| Area | Status |
|---|---|
| URL scheme/host validation | Addressed, tested |
| Private/internal IP-literal blocking | Addressed, tested |
| DNS-based internal-target bypass | **Unresolved** — not checked |
| Rate limiting | **Not implemented** — open gap |
| Input validation (length, format) | Addressed |
| Error leakage | Addressed (same pattern as prior phases) |
| Analytics privacy | Addressed by minimal collection |

No secrets are involved in this feature's data model. No new logging of sensitive content was introduced.
