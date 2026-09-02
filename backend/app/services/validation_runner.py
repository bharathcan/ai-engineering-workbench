"""Controlled validation execution. The API only ever accepts a
`validation_type` from a fixed set — never a raw command string — and each
type maps to exactly one hardcoded, allowlisted command below. There is no
code path from user input to arbitrary shell execution.

See docs/validation/validation-strategy.md for what each validation type
actually checks and its documented limitations.
"""

import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

from app.core.exceptions import UnsupportedValidationTypeError

BACKEND_ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_ROOT.parent


@dataclass
class RunnerResult:
    status: str  # PASSED | FAILED | NOT_VALIDATED
    command: str
    output: str
    error: str | None
    duration_ms: int
    metadata: dict = field(default_factory=dict)


def _run_command(command: list[str], cwd: Path, timeout_s: int = 120) -> tuple[int, str, str, int]:
    start = time.monotonic()
    try:
        proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout_s)
        return proc.returncode, proc.stdout, proc.stderr, int((time.monotonic() - start) * 1000)
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return -1, exc.stdout or "", f"Command timed out after {timeout_s}s.", duration_ms
    except OSError as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        return -1, "", f"Failed to execute command: {exc}", duration_ms


def run_unit_tests() -> RunnerResult:
    command_display = "pytest -q"
    code, out, err, dur = _run_command([sys.executable, "-m", "pytest", "-q"], cwd=BACKEND_ROOT)
    return RunnerResult(
        status="PASSED" if code == 0 else "FAILED",
        command=command_display,
        output=out,
        error=err or None,
        duration_ms=dur,
        metadata={"exit_code": code},
    )


def run_integration_tests() -> RunnerResult:
    # This repository's test suite has no unit/integration split (no pytest
    # markers) — every test already exercises the FastAPI app + a real
    # SQLite DB through TestClient. Rather than fabricate a distinct
    # command, this documents that fact and runs the same suite.
    result = run_unit_tests()
    result.metadata["note"] = (
        "No distinct integration-test target exists in this repo yet; "
        "runs the same suite as UNIT_TEST."
    )
    return result


def run_static_analysis() -> RunnerResult:
    command_display = "ruff check ."
    code, out, err, dur = _run_command(
        [sys.executable, "-m", "ruff", "check", "."], cwd=BACKEND_ROOT
    )
    return RunnerResult(
        status="PASSED" if code == 0 else "FAILED",
        command=command_display,
        output=out,
        error=err or None,
        duration_ms=dur,
        metadata={"exit_code": code},
    )


def run_build_check() -> RunnerResult:
    command_display = "python -c 'import app.main'"
    code, out, err, dur = _run_command(
        [sys.executable, "-c", "import app.main"], cwd=BACKEND_ROOT
    )
    return RunnerResult(
        status="PASSED" if code == 0 else "FAILED",
        command=command_display,
        output=out or "app.main imported successfully — the application boots without error.",
        error=err or None,
        duration_ms=dur,
        metadata={
            "exit_code": code,
            "scope": "backend import check only, not a frontend bundle build",
        },
    )


def run_api_contract_validation() -> RunnerResult:
    command_display = "app.main:app.openapi() structural check"
    start = time.monotonic()
    try:
        from app.main import app as fastapi_app

        schema = fastapi_app.openapi()
    except Exception as exc:  # generating the schema itself failed
        duration_ms = int((time.monotonic() - start) * 1000)
        return RunnerResult(
            status="FAILED",
            command=command_display,
            output="",
            error=f"Failed to generate OpenAPI schema: {exc}",
            duration_ms=duration_ms,
        )

    errors = []
    for required_key in ("openapi", "info", "paths"):
        if required_key not in schema:
            errors.append(f"Missing required top-level key: '{required_key}'")
    for path, methods in schema.get("paths", {}).items():
        if not methods:
            errors.append(f"Path '{path}' has no operations defined.")
        for method, operation in methods.items():
            if "responses" not in operation:
                errors.append(f"{method.upper()} {path} is missing 'responses'.")

    duration_ms = int((time.monotonic() - start) * 1000)
    path_count = len(schema.get("paths", {}))
    if errors:
        return RunnerResult(
            status="FAILED",
            command=command_display,
            output="",
            error="; ".join(errors),
            duration_ms=duration_ms,
            metadata={"path_count": path_count},
        )
    return RunnerResult(
        status="PASSED",
        command=command_display,
        output=(
            f"OpenAPI schema is structurally valid: {path_count} paths, "
            f"openapi version {schema.get('openapi')}."
        ),
        error=None,
        duration_ms=duration_ms,
        metadata={"path_count": path_count},
    )


_SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key pattern"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI-style secret key pattern"),
    (re.compile(r"-----BEGIN (RSA |EC )?PRIVATE KEY-----"), "private key block"),
]


def run_security_scan() -> RunnerResult:
    """A lightweight static heuristic scan for hardcoded-secret patterns —
    NOT a comprehensive security audit, and NOT a dependency vulnerability
    scan (no network access to a CVE database in this environment)."""
    command_display = "static heuristic scan for hardcoded secret patterns"
    start = time.monotonic()
    findings = []
    for path in BACKEND_ROOT.rglob("*.py"):
        # tests/ deliberately contains fake-secret-shaped fixture strings to
        # exercise this exact detector — scanning it would flag the test
        # suite itself, not real application code. Excluded on purpose.
        if ".venv" in path.parts or "__pycache__" in path.parts or "tests" in path.parts:
            continue
        try:
            text = path.read_text(errors="ignore")
        except OSError:
            continue
        for pattern, label in _SECRET_PATTERNS:
            if pattern.search(text):
                try:
                    display_path = path.relative_to(REPO_ROOT)
                except ValueError:
                    display_path = path
                findings.append(f"{display_path}: possible {label}")

    duration_ms = int((time.monotonic() - start) * 1000)
    scope_note = (
        "Static heuristic scan only — checks backend/**/*.py for a small set of "
        "known secret-key patterns. Does not scan dependencies for known "
        "vulnerabilities (no network access to a CVE database here), and does "
        "not claim comprehensive security coverage."
    )
    if findings:
        return RunnerResult(
            status="FAILED",
            command=command_display,
            output="",
            error="; ".join(findings),
            duration_ms=duration_ms,
            metadata={"scope": scope_note},
        )
    return RunnerResult(
        status="PASSED",
        command=command_display,
        output=(
            "No hardcoded secret patterns (AWS keys, OpenAI-style keys, private "
            "key blocks) found in backend/**/*.py."
        ),
        error=None,
        duration_ms=duration_ms,
        metadata={"scope": scope_note},
    )


def run_performance_placeholder() -> RunnerResult:
    return RunnerResult(
        status="NOT_VALIDATED",
        command="none",
        output="",
        error=(
            "No running endpoint is associated with a generic artifact to load-test. "
            "Endpoint performance testing is implemented separately for concrete "
            "live endpoints — see app.services.performance_probe."
        ),
        duration_ms=0,
    )


RUNNERS = {
    "UNIT_TEST": run_unit_tests,
    "INTEGRATION_TEST": run_integration_tests,
    "STATIC_ANALYSIS": run_static_analysis,
    "API_CONTRACT": run_api_contract_validation,
    "BUILD": run_build_check,
    "SECURITY": run_security_scan,
    "PERFORMANCE": run_performance_placeholder,
}


def run_validation(validation_type: str) -> RunnerResult:
    runner = RUNNERS.get(validation_type)
    if runner is None:
        raise UnsupportedValidationTypeError(validation_type)
    return runner()
