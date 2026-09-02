"""Payloads for the Phase 9 brownfield scenario — see
tests/test_brownfield_performance_flow.py and docs/scenarios/brownfield.md.

No live AI provider is configured in this environment — this content is
engineer-authored, standing in for a provider response, exactly as in every
prior phase's test fixtures. It reflects the REAL bottleneck identified by
reading app/services/url_service.py (see docs/scenarios/brownfield.md),
not a fictional one.
"""

BROWNFIELD_ANALYSIS = {
    "summary": (
        "Improve GET /{short_code} redirect performance without changing its public "
        "request/response contract."
    ),
    "functional_requirements": [
        {"id": "FR-001", "description": "Improve the redirect endpoint's response latency."},
    ],
    "non_functional_requirements": [
        {
            "id": "NFR-001",
            "description": (
                "The public API contract for GET /{short_code} (status codes, response "
                "shape, headers) must not change."
            ),
        },
    ],
    "ambiguities": [
        {
            "id": "AMB-001",
            "description": (
                "\"Slow\" is not quantified — no baseline latency number or target "
                "threshold is given."
            ),
            "why_it_matters": (
                "Without a number, there is no way to confirm whether any given "
                "measurement counts as \"slow\", or how much improvement counts as "
                "\"improved\"."
            ),
            "impact": "MEDIUM",
            "information_needed": "An actual baseline measurement and a target, if one exists.",
        },
    ],
    "assumptions": [
        {
            "id": "ASM-001",
            "description": (
                "\"Performance\" refers to this server's own response latency, not "
                "client-side network latency, which this system does not control."
            ),
            "reason": (
                "The requirement only describes the service's behavior, not the network path."
            ),
            "impact": (
                "Scopes the investigation to server-side code, not infrastructure/network changes."
            ),
        },
    ],
    "constraints": [
        {
            "id": "CON-001",
            "description": "The public API of GET /{short_code} must not change.",
        },
    ],
    "success_criteria": [
        {
            "id": "SC-001",
            "description": (
                "A real, measured before/after latency comparison shows improvement, "
                "with the public response contract verified unchanged."
            ),
        },
    ],
    "engineering_concerns": [
        {
            "id": "ENG-001",
            "description": (
                "A real baseline must be measured before assuming what the bottleneck is "
                "or reaching for a specific fix (e.g. a cache) without evidence it's needed."
            ),
        },
    ],
}

BROWNFIELD_PLAN = {
    "summary": "Analyze, identify, and fix the redirect path's actual latency bottleneck.",
    "tasks": [
        {
            "id": "TASK-001",
            "title": "Analyze current redirect performance",
            "description": (
                "Measure real baseline latency for GET /{short_code} and read the current "
                "implementation to identify what it's actually doing per request."
            ),
            "type": "PERFORMANCE",
            "requirement_refs": ["FR-001", "ENG-001"],
            "dependencies": [],
            "sequence": 1,
            "acceptance_criteria": [
                "A real, measured baseline exists (not estimated).",
                "The current code path's per-request work is enumerated.",
            ],
            "ai_assistance_type": "PERFORMANCE_REVIEW",
            "risks": [],
        },
        {
            "id": "TASK-002",
            "title": "Identify the actual bottleneck",
            "description": (
                "Determine, from the code and the baseline, what specifically contributes "
                "to redirect latency — without assuming a cache is the answer."
            ),
            "type": "PERFORMANCE",
            "requirement_refs": ["ENG-001"],
            "dependencies": ["TASK-001"],
            "sequence": 2,
            "acceptance_criteria": [
                "A specific, code-level cause is identified, not a generic guess.",
            ],
            "ai_assistance_type": "DESIGN",
            "risks": [],
        },
        {
            "id": "TASK-003",
            "title": "Implement the optimization",
            "description": (
                "Change the redirect path so the click-recording write no longer blocks "
                "the redirect response, without changing the public API."
            ),
            "type": "BACKEND",
            "requirement_refs": ["FR-001", "CON-001"],
            "dependencies": ["TASK-002"],
            "sequence": 3,
            "acceptance_criteria": [
                "GET /{short_code}'s response status/shape/headers are unchanged.",
                "Existing tests still pass unmodified.",
            ],
            "ai_assistance_type": "CODE_GENERATION",
            "risks": [
                {
                    "id": "RISK-001",
                    "description": (
                        "Deferring the click write could lose the click if the process "
                        "crashes between responding and the write completing."
                    ),
                    "impact": "LOW",
                },
            ],
        },
        {
            "id": "TASK-004",
            "title": "Regression test and re-measure",
            "description": (
                "Run the full existing test suite unmodified, add a regression test "
                "confirming API compatibility, and re-measure latency for comparison."
            ),
            "type": "TESTING",
            "requirement_refs": ["NFR-001", "SC-001"],
            "dependencies": ["TASK-003"],
            "sequence": 4,
            "acceptance_criteria": [
                "All pre-existing tests pass without modification.",
                "A real before/after latency comparison is recorded.",
            ],
            "ai_assistance_type": "TEST_GENERATION",
            "risks": [],
        },
    ],
    "assumptions": [
        "The redirect path's current implementation is the primary lever available — "
        "infrastructure changes (e.g. a faster disk, a different DB engine) are out of scope.",
    ],
    "risks": [],
}
