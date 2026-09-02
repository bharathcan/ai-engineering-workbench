"""Example AI-recommendation payloads for task-level AI assistance tests."""

VALID_RECOMMENDATION = {
    "summary": "Use a unique database constraint.",
    "approach": "Generate the code and retry on collision.",
    "files_to_change": ["url_service.py"],
    "proposed_changes": ["Add uniqueness constraint"],
    "tests_to_add": ["test_collision_retry"],
    "risks": ["High concurrency may require additional testing."],
    "assumptions": [],
    "confidence": "MEDIUM",
}

HIGH_CONFIDENCE_RECOMMENDATION = {
    **VALID_RECOMMENDATION,
    "confidence": "HIGH",
}
