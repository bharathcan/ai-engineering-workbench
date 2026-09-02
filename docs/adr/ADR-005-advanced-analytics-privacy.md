# ADR-005: Advanced User Analytics — Privacy-Conscious Implementation

## Status

Accepted — Phase 10 (post-decision implementation). Implemented in `backend/app/models/url.py` (`ClickEvent`), `backend/app/services/click_analytics.py`, `backend/app/services/user_agent.py`, `GET /api/v1/urls/{short_code}/analytics/advanced`.

## Context

Phase 10's ambiguous requirement — "Improve the analytics." — was correctly blocked by the Task Decomposer's ambiguity gate (`docs/REQUIREMENTS.md` AMB-002, `AMB-001` in this scenario's own analysis) rather than letting AI silently pick a scope. Three interpretations were presented; **the engineer explicitly chose Interpretation C — Advanced User Analytics** (geographic, device, referrer, behavioral data).

This directly **reopens the decision made in [ADR-004](ADR-004-analytics-design.md)**, which chose click-count + timestamp only, specifically citing privacy-by-minimalism: "collecting less means less to protect." ADR-004's reasoning was correct *for the scope it addressed* — nothing had asked for more at that point. It does not apply here: the engineer has now explicitly asked for more, with the trade-off understood (the option's own stated con in the Phase 10 presentation was "additional data collection, privacy/security implications, increased complexity"). **This ADR does not overrule ADR-004 — it documents a new, explicit decision for a newly-in-scope requirement, and implements it with privacy mitigations even though the broader feature was chosen.**

## Decision

Implement device type, browser, referrer, and repeat-visitor tracking per click, via a new `ClickEvent` table — **with the following privacy mitigations, applied regardless of the interpretation chosen:**

1. **Never store the raw client IP.** Only a salted SHA-256 hash (`app.services.click_analytics.hash_ip`), used solely to derive `is_repeat_visitor`. The hash cannot be reversed to the original IP without the salt, and the salt is not hardcoded in source (generated at process startup unless explicitly configured — see `Settings.ip_hash_salt`).
2. **Do not fabricate geographic data.** No GeoIP database or lookup service exists in this environment. Rather than skip geographic entirely (which the engineer did not choose) or fake it (which would violate this project's core validation-integrity principle), the API returns an explicit `geographic_status` field stating why it's unavailable, with an empty `geographic_breakdown` — never a silently-wrong or invented location.
3. **User-Agent is classified into two coarse categories (`device_type`, `browser`), not exposed as the raw string in any aggregate response.** The raw `user_agent` is stored (needed to actually do the classification and for potential re-classification later), but analytics responses only ever return the derived category, not the raw string.

## Alternatives Considered

### Option A — Implement exactly as requested, no mitigations

Store raw IP, raw User-Agent, and skip the geographic gap by silently omitting it without explanation.

**Rejected:** storing raw IP when a hash serves the same purpose (repeat-visitor detection) is unnecessary risk with no offsetting benefit. Silently omitting geography without explanation would look like an oversight rather than a disclosed limitation — inconsistent with this project's validation-integrity principle applied everywhere else.

### Option B — Refuse to implement geographic/behavioral scope at all, only do device+referrer

Partially implement Interpretation C, silently dropping the parts requiring more infrastructure.

**Rejected:** this would be a second silent narrowing of engineer-chosen scope by AI — exactly what Phase 10 exists to prevent. If geographic data isn't implementable honestly right now, the correct response is to say so explicitly (which this ADR does), not to quietly implement less than what was asked and let it pass unremarked.

### Option C — Implement with disclosed mitigations (chosen)

As described in Decision above: build what was asked, minimize what's collected wherever it doesn't reduce the feature's actual value (hashing IP costs nothing functionally, since only equality/repeat-detection is needed), and be explicit about what genuinely isn't implemented and why.

## Recommendation

**Option C.** The engineer's choice of scope is respected in full — nothing requested is silently dropped — while every place a *how* decision was still open (raw vs. hashed IP, fabricated vs. honestly-absent geography) applies the same privacy/integrity principles this project has used everywhere else, rather than treating "the engineer chose the more invasive option" as license to stop being careful.

## Consequences

* `GET /api/v1/urls/{short_code}/analytics/advanced` returns device/browser/referrer breakdowns and a repeat-visitor rate, immediately usable.
* Geographic breakdown will require a real GeoIP data source (a local database file or a network lookup service) to ever return real data — this ADR does not resolve that, it discloses it.
* If `IP_HASH_SALT` is not configured via environment variable, repeat-visitor detection resets across process restarts (a random salt is generated each time) — acceptable for this phase, but worth configuring explicitly for any deployment where that continuity matters.

## Trade-offs

* **Privacy vs. completeness** — hashing IP instead of storing it raw loses the ability to ever retroactively add geographic resolution to *already-collected* events (the raw IP is gone). This is accepted deliberately: the mitigation is the point.
* **Honesty vs. apparent completeness** — an empty geographic breakdown with an explanatory status is less impressive-looking than a populated (but fake) one. This is the correct trade to make.

## Risks

* The User-Agent classifier (`app/services/user_agent.py`) is a lightweight heuristic, not a maintained device database — it will misclassify uncommon or spoofed User-Agent strings. Documented in the module itself, not claimed to be authoritative.
* Even hashed, IP-derived repeat-visitor tracking is still a form of user tracking across visits — smaller in scope than raw IP storage, but not zero. This is inherent to "behavioral" analytics as an interpretation choice, not something this ADR's mitigations eliminate entirely.
* No legal/compliance review (e.g., GDPR/CCPA applicability) has been performed — this is an engineering privacy-minimization decision, not a substitute for one. ⚠ **ENGINEERING REVIEW REQUIRED** before any real deployment collecting this data from real users.

## Validation

`backend/tests/test_click_analytics.py` confirms the hash is deterministic, differs per input, and never contains the raw IP as a substring of its own output. `backend/tests/test_advanced_analytics_api.py` confirms the API response never includes an `ip_hash`/`ip_address` field, confirms repeat-visitor detection actually works end-to-end, and confirms the geographic fields are honestly empty with a stated reason rather than fabricated. **Not validated:** classifier accuracy against a broad, real-world sample of User-Agent strings (only a handful of common ones are tested); behavior under a configured, persistent `IP_HASH_SALT` (only the random-default path is exercised).
