import pytest

from app.core.exceptions import UnsafeArtifactPathError
from app.utils.safe_path import ARTIFACT_WORKSPACE_ROOT, resolve_artifact_path


def test_valid_relative_path_resolves_inside_workspace():
    resolved = resolve_artifact_path("backend/app/services/url_service.py")
    assert resolved.is_relative_to(ARTIFACT_WORKSPACE_ROOT)
    assert resolved == ARTIFACT_WORKSPACE_ROOT / "backend/app/services/url_service.py"


def test_empty_path_is_rejected():
    with pytest.raises(UnsafeArtifactPathError):
        resolve_artifact_path("")


def test_whitespace_only_path_is_rejected():
    with pytest.raises(UnsafeArtifactPathError):
        resolve_artifact_path("   ")


def test_absolute_path_is_rejected():
    with pytest.raises(UnsafeArtifactPathError, match="absolute"):
        resolve_artifact_path("/etc/passwd")


def test_parent_traversal_is_rejected():
    with pytest.raises(UnsafeArtifactPathError, match=r"\.\."):
        resolve_artifact_path("../../.env")


def test_parent_traversal_mid_path_is_rejected():
    with pytest.raises(UnsafeArtifactPathError, match=r"\.\."):
        resolve_artifact_path("backend/../../../etc/passwd")


def test_dotenv_style_traversal_from_workspace_root_is_rejected():
    with pytest.raises(UnsafeArtifactPathError):
        resolve_artifact_path("../.env")
