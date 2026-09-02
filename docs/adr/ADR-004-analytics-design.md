# ADR-004: Analytics Design

## Status

Accepted — Phase 8G. Implemented in `backend/app/models/url.py` (`click_count`, `last_accessed_at`) and `GET /api/v1/urls/{short_code}/analytics`.

## Context

`docs/REQUIREMENTS.md` URL-FR-005 requires "analytics," but — per AMB-002 in that same document — never specifies what "analytics" means beyond that. This ADR scopes what's actually built and explains why nothing more was added.

## Decision

**Track exactly two things per URL: a click count, and the timestamp of the most recent click.** No per-click event log, no geography/device/referrer data, no separate analytics table.

## Reasoning

Requirements say the mandatory scope is "analytics," and section 8G of the workbench instructions explicitly frames click count + timestamp as the evaluated minimum, with anything beyond that requiring justification. There is no stated justification in this requirement for anything more:

* No consumer of richer analytics (a dashboard, a report, a specific business question) is named.
* Per-click event storage (IP, user-agent, referrer, geo) would also introduce a **privacy question this requirement never asked to be answered** — collecting it "because we could" is scope creep with a real cost (it becomes data that has to be protected, retained-with-a-policy, and justified under whatever privacy posture this system eventually needs), not a neutral default.
* This mirrors the same reasoning already applied in ADR-003: don't build infrastructure (here, an events pipeline) that nothing has actually asked for yet.

Two fields on the existing `shortened_urls` row (rather than a separate events table) keeps this genuinely minimal: it answers "how many times, and when last" — the two things explicitly named — without implying a scale of data collection nothing has justified.

## Alternatives Considered

### Option A — Per-click event table (timestamp, and whatever else)

A `url_clicks` row per click, enabling time-series queries (clicks per day, etc.) later.

**Pros:** More flexible for future questions ("clicks over time" rather than just "clicks total"). **Cons:** unbounded growth with no retention policy defined (another unresolved ambiguity, `docs/REQUIREMENTS.md` AMB-009), and — per the workbench's own explicit instruction — "do not introduce Kafka/event streaming simply to appear scalable" applies in spirit here too: a write-heavy events table for a requirement that only asked for "click count + timestamp" is more infrastructure than the requirement supports.

### Option B — Two fields on the URL row (chosen)

`click_count: int`, `last_accessed_at: datetime | None`, incremented/updated atomically on every successful redirect (`app.repositories.url_repository.record_click`).

## Recommendation

**Option B.** It satisfies exactly what's named in the requirement and the workbench's own evaluated minimum, without inventing scope (a time-series capability, PII collection) the requirement never asked for. If a real future requirement asks for "clicks over time" or "clicks by referrer," that is new scope, not an extension of this one — it should go through the same requirement-analysis → ambiguity-detection process as everything else in this workbench, not be pre-built speculatively now.

## Consequences

* `GET /api/v1/urls/{short_code}/analytics` can answer "how many times has this been clicked, and when last" — and nothing else.
* A redirect and a click-count increment happen in the same request (`resolve_and_record_click`) — the click is recorded as part of resolving the redirect, so a click that reaches this server counts even if the client never follows the resulting `Location` header. What this can't distinguish: a bot/crawler hit vs. a human click, or a retried request vs. two distinct visits — both are logged identically, since nothing beyond count+timestamp was scoped.

## Trade-offs

* **Minimalism vs. future flexibility** — deliberately not building toward hypothetical future questions ("clicks per day," "top referrers") this requirement never asked.
* **Privacy-by-minimalism** — collecting less means less to protect, at the cost of less analytical depth if it's ever actually wanted.

## Risks

* If "improve the analytics" (the Phase 10 ambiguous scenario) or a future real requirement calls for materially more than this, click history prior to that point cannot be reconstructed — there is no raw event log to retroactively query, only the running totals kept here. This is a direct, acknowledged consequence of Option B's minimalism, not an oversight.

## Validation

`backend/tests/test_urls_api.py::test_redirect_increments_click_count_and_updates_timestamp` actually exercises this: two real redirects against a real (test) DB, then a real `GET .../analytics` call confirming `click_count == 2` and `last_accessed_at` is set. Not validated: behavior under concurrent redirects to the same code (same limitation noted in ADR-002 — no multi-threaded test harness in this environment).
