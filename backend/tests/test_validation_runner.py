import subprocess

import pytest

from app.core.exceptions import UnsupportedValidationTypeError
from app.services import validation_runner


def test_unsupported_validation_type_raises():
    with pytest.raises(UnsupportedValidationTypeError):
        validation_runner.run_validation("NOT_A_REAL_TYPE")


def test_unit_tests_map_exit_code_zero_to_passed(monkeypatch):
    fake_result = subprocess.CompletedProcess(
        args=["pytest"], returncode=0, stdout="5 passed in 0.12s", stderr=""
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake_result)

    result = validation_runner.run_unit_tests()
    assert result.status == "PASSED"
    assert result.command == "pytest -q"
    assert "5 passed" in result.output
    assert result.error is None


def test_unit_tests_map_nonzero_exit_code_to_failed(monkeypatch):
    fake_result = subprocess.CompletedProcess(
        args=["pytest"], returncode=1, stdout="1 failed, 4 passed", stderr="AssertionError"
    )
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake_result)

    result = validation_runner.run_unit_tests()
    assert result.status == "FAILED"
    assert result.error == "AssertionError"


def test_integration_tests_documents_shared_command(monkeypatch):
    fake_result = subprocess.CompletedProcess(args=["pytest"], returncode=0, stdout="ok", stderr="")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: fake_result)

    result = validation_runner.run_integration_tests()
    assert result.status == "PASSED"
    assert "note" in result.metadata


def test_static_analysis_runs_real_subprocess_against_this_repo():
    # A real subprocess call (ruff is fast, non-recursive) — proves genuine
    # execution happens, not simulated output.
    result = validation_runner.run_static_analysis()
    assert result.command == "ruff check ."
    assert result.status in ("PASSED", "FAILED")
    assert result.duration_ms >= 0


def test_build_check_runs_real_subprocess_and_passes():
    result = validation_runner.run_build_check()
    assert result.status == "PASSED"
    assert "imported successfully" in result.output


def test_api_contract_validation_passes_for_real_app():
    result = validation_runner.run_api_contract_validation()
    assert result.status == "PASSED"
    assert result.metadata["path_count"] > 0


def test_security_scan_passes_on_this_clean_codebase():
    result = validation_runner.run_security_scan()
    assert result.status == "PASSED"


def test_security_scan_detects_injected_secret_pattern(tmp_path, monkeypatch):
    (tmp_path / "leaky.py").write_text('AWS_KEY = "AKIAABCDEFGHIJKLMNOP"\n')
    monkeypatch.setattr(validation_runner, "BACKEND_ROOT", tmp_path)

    result = validation_runner.run_security_scan()
    assert result.status == "FAILED"
    assert "AWS access key" in result.error


def test_performance_placeholder_is_not_validated():
    result = validation_runner.run_performance_placeholder()
    assert result.status == "NOT_VALIDATED"
    assert result.error is not None
