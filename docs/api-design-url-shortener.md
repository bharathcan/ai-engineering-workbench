# API Design — URL Shortener

> This documents the **URL shortener's own API** — the mandatory demonstration use case (Phase 8) built *through* the workbench. It is a separate document from [api-design.md](api-design.md), which covers the workbench's own meta-API (requirements, tasks, AI runs, artifacts, validations) — the two are different domains that happen to share one FastAPI app for simplicity. See `ARCHITECTURE.md` and `backend/tests/test_url_shortener_workbench_flow.py` for how this feature's own requirement/plan/task/AI-run/artifact/validation chain was actually processed through that workbench API.

## POST /api/v1/urls

Creates a shortened URL mapping (URL-FR-001, URL-FR-004).

**Request body**

```json
{ "original_url": "https://example.com/some/page", "expires_at": null }
```

`original_url`: required, non-empty, ≤2048 chars, must be `http`/`https`, must have a host, and must not target `localhost` or a private/loopback/link-local/reserved IP literal (see [validation/PHASE-8-SECURITY-REVIEW.md](validation/PHASE-8-SECURITY-REVIEW.md)). `expires_at`: optional ISO 8601 datetime.

**Response — `201 Created`**

```json
{
  "id": "URL-001",
  "short_code": "6HZUtPB",
  "original_url": "https://example.com/some/page",
  "status": "ACTIVE",
  "created_at": "2026-01-01T00:00:00+00:00",
  "expires_at": null
}
```

`short_code` is a random 7-character Base62 string (`app/services/short_code.py`) — see [ADR-002](adr/ADR-002-short-code-strategy.md) for why random rather than sequential, and how collisions are handled (DB-enforced retry, not a pre-check).

**Errors**

| Status | Cause |
|---|---|
| 422 | Invalid `original_url` (bad scheme, empty, too long, private/internal target) |
| 503 | Every collision-retry attempt failed (`ShortCodeGenerationExhaustedError`) — practically unreachable at today's keyspace size |
| 500 | Persistence failure |

## GET /{short_code}

Resolves a short code and redirects to its destination (URL-FR-002). **Not under `/api/v1`** — a short link is meant to be short. Registered last in the app so it never shadows a more specific route (`/health`, `/docs`, `/api/v1/...`).

**Response — `307 Temporary Redirect`**, `Location` header set to the original URL. **307, not 301/308** — a permanent redirect status invites browsers to cache it and stop hitting this server on future visits, which would silently undercount clicks (see [ADR-004](adr/ADR-004-analytics-design.md)). A successful redirect also records the click (`click_count`/`last_accessed_at`) as part of resolving — the click is counted as soon as it reaches this server, regardless of whether the client follows the `Location` header.

**Errors**

| Status | Cause |
|---|---|
| 404 | No URL exists with that short code |
| 410 | The URL exists but has expired (`expires_at` in the past) or been disabled (`status != "ACTIVE"`) — distinct from 404: it existed, it's just no longer available |
| 500 | Persistence failure |

`short_code` in the path is constrained to `^[0-9A-Za-z]{4,16}$` — anything outside that shape 404s at routing, never reaching the lookup.

## GET /api/v1/urls/{short_code}/analytics

Retrieves the minimum analytics scoped for this phase (URL-FR-005) — see [ADR-004](adr/ADR-004-analytics-design.md) for why only these two fields, not richer per-click data.

**Response — `200 OK`**

```json
{
  "short_code": "6HZUtPB",
  "click_count": 1,
  "created_at": "2026-01-01T00:00:00+00:00",
  "last_accessed_at": "2026-01-01T00:00:05+00:00"
}
```

**Errors**: `404` (unknown short code), `500` (persistence failure).

## GET /api/v1/urls/{short_code}/analytics/advanced

**Interpretation C from the Phase 10 ambiguous-requirement scenario** (the engineer's explicit choice, not an AI assumption) — see [ADR-005](adr/ADR-005-advanced-analytics-privacy.md). Does not replace the basic analytics endpoint above; both exist.

**Response — `200 OK`**

```json
{
  "short_code": "6HZUtPB",
  "total_events": 2,
  "device_breakdown": [{ "key": "MOBILE", "count": 1 }, { "key": "DESKTOP", "count": 1 }],
  "browser_breakdown": [{ "key": "SAFARI", "count": 1 }, { "key": "CHROME", "count": 1 }],
  "referrer_breakdown": [{ "key": "https://twitter.com/post/1", "count": 1 }],
  "repeat_visitor_count": 1,
  "repeat_visitor_rate": 0.5,
  "geographic_breakdown": [],
  "geographic_status": "Not implemented: no GeoIP data source is available in this environment. IP is hashed for repeat-visitor detection only, never resolved to a location."
}
```

**Privacy, by construction, not just policy**: this response can never contain a raw client IP or a raw User-Agent string — only derived `device_type`/`browser` categories and a hashed-IP-derived repeat-visitor signal. `geographic_breakdown` is always empty with `geographic_status` stating why — never fabricated. See [ADR-005](adr/ADR-005-advanced-analytics-privacy.md).

**Errors**: `404` (unknown short code), `500` (persistence failure).

## What's explicitly not built

* **No update/disable/delete endpoint** — `status` exists on the model (`ACTIVE`/`DISABLED`) but nothing sets it to `DISABLED` yet; not scoped by the mandatory requirement.
* **No rate limiting** — disclosed as an open gap in [validation/PHASE-8-SECURITY-REVIEW.md](validation/PHASE-8-SECURITY-REVIEW.md), not silently missing.
* **No geographic resolution** — no GeoIP data source exists in this environment; disclosed via `geographic_status` on every advanced-analytics response, not silently omitted. See [ADR-005](adr/ADR-005-advanced-analytics-privacy.md).
* **No cache** — a deliberate decision, not a gap; see [ADR-003](adr/ADR-003-cache-strategy.md).
