"""Payloads for tests/test_advanced_analytics_workbench_flow.py — the
Phase 10 ambiguous-requirement scenario after the engineer's decision.

No live AI provider is configured in this environment — this content is
engineer-authored, standing in for a provider response, exactly as in
every prior phase's test fixtures.
"""

CLARIFIED_REQUIREMENT_TEXT = (
    "Improve the analytics by adding advanced user analytics: track device type, "
    "browser, referrer, and repeat-visitor behavior for each redirect click. "
    "(Engineer decision: Interpretation C from the Phase 10 ambiguous-requirement "
    "review — see docs/adr/ADR-005-advanced-analytics-privacy.md.)"
)

CLARIFIED_ANALYSIS = {
    "summary": (
        "Add per-click device, browser, referrer, and repeat-visitor tracking to the "
        "URL shortener's analytics, per the engineer's chosen interpretation."
    ),
    "functional_requirements": [
        {"id": "FR-001", "description": "Record device type for each redirect click."},
        {"id": "FR-002", "description": "Record browser for each redirect click."},
        {"id": "FR-003", "description": "Record referrer for each redirect click."},
        {"id": "FR-004", "description": "Detect and report repeat-visitor clicks."},
    ],
    "non_functional_requirements": [
        {
            "id": "NFR-001",
            "description": "Client IP must not be stored in raw form (privacy minimization).",
        },
    ],
    "ambiguities": [
        {
            "id": "AMB-001",
            "description": "No GeoIP data source is available to resolve geographic location.",
            "why_it_matters": "Geographic breakdown was part of the chosen interpretation's scope.",
            "impact": "LOW",
            "information_needed": "A GeoIP database or lookup service, if geography is required.",
        },
    ],
    "assumptions": [],
    "constraints": [
        {"id": "CON-001", "description": "Must not change the existing basic analytics contract."},
    ],
    "success_criteria": [
        {
            "id": "SC-001",
            "description": (
                "GET /api/v1/urls/{short_code}/analytics/advanced returns device, browser, "
                "referrer, and repeat-visitor breakdowns without exposing raw IP."
            ),
        },
    ],
    "engineering_concerns": [
        {
            "id": "ENG-001",
            "description": (
                "This directly reopens ADR-004's privacy-by-minimalism decision — must be "
                "implemented with its own privacy mitigations, not just flipped on."
            ),
        },
    ],
}

CLARIFIED_PLAN = {
    "summary": "Implement per-click advanced analytics with privacy mitigations.",
    "tasks": [
        {
            "id": "TASK-001",
            "title": "Add ClickEvent model and hashed-IP capture",
            "description": (
                "Add a per-click event table capturing device/browser/referrer and a "
                "hashed (never raw) client IP for repeat-visitor detection."
            ),
            "type": "DATABASE",
            "requirement_refs": ["FR-001", "FR-002", "FR-003", "NFR-001"],
            "dependencies": [],
            "sequence": 1,
            "acceptance_criteria": [
                "Raw client IP is never persisted.",
                "Device and browser are derived from the User-Agent header.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [
                {
                    "id": "RISK-001",
                    "description": "Device/browser classification is heuristic, not authoritative.",
                    "impact": "LOW",
                },
            ],
        },
        {
            "id": "TASK-002",
            "title": "Expose advanced analytics endpoint",
            "description": (
                "Add GET /api/v1/urls/{short_code}/analytics/advanced returning aggregated "
                "breakdowns, with an honest, non-fabricated geographic status."
            ),
            "type": "API",
            "requirement_refs": ["FR-004", "SC-001"],
            "dependencies": ["TASK-001"],
            "sequence": 2,
            "acceptance_criteria": [
                "Response never includes raw IP or a fabricated geographic value.",
                "Existing GET .../analytics contract is unchanged.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [],
        },
    ],
    "assumptions": [],
    "risks": [
        {
            "id": "RISK-002",
            "description": "No legal/compliance review of this data collection has been performed.",
            "impact": "MEDIUM",
        },
    ],
}

CLICK_EVENT_RECOMMENDATION = {
    "summary": "Add ClickEvent with hashed IP and derived device/browser categories.",
    "approach": (
        "Add a ClickEvent table linked to ShortenedUrl, populated in the same deferred "
        "background task as the existing click-count write (Phase 9). Hash the client IP "
        "with a salted SHA-256 before storage; classify device/browser from the User-Agent "
        "header via a lightweight heuristic; never resolve geography (no data source exists)."
    ),
    "files_to_change": [
        "backend/app/models/url.py",
        "backend/app/services/click_analytics.py",
        "backend/app/services/user_agent.py",
        "backend/app/repositories/click_event_repository.py",
    ],
    "proposed_changes": [
        "Add ClickEvent model with ip_hash (never raw IP).",
        "Add hash_ip() using a salted SHA-256.",
        "Add classify_device()/classify_browser() heuristics.",
        "Add click_event_repository with has_prior_click() and save_click_event().",
    ],
    "tests_to_add": [
        "test_hash_ip_never_contains_the_raw_ip",
        "test_repeat_visitor_detected_via_hashed_ip_not_raw_ip",
    ],
    "risks": [
        "Heuristic UA classification will misclassify uncommon or spoofed User-Agent strings.",
    ],
    "assumptions": [],
    "confidence": "MEDIUM",
}
