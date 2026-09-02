"""Path containment for artifact writes. AI-proposed artifact paths must
never resolve outside the approved generated/ workspace — see
docs/api-design.md 'Controlled File Writes'."""

from pathlib import Path

from app.core.exceptions import UnsafeArtifactPathError

# backend/app/utils/safe_path.py -> parents[3] is the repo root (generated/
# is a sibling of backend/, established as the workbench's designated
# artifact workspace since Phase 1A — see ARCHITECTURE.md).
_REPO_ROOT = Path(__file__).resolve().parents[3]
ARTIFACT_WORKSPACE_ROOT = (_REPO_ROOT / "generated").resolve()


def resolve_artifact_path(relative_path: str) -> Path:
    """Returns the absolute on-disk path for a proposed artifact path, or
    raises UnsafeArtifactPathError if it would write outside the workspace.

    Two checks, deliberately redundant: an explicit rejection of absolute
    paths and '..' segments (so the error names the actual problem), and a
    resolved-path containment check afterward (so no encoding or symlink
    trick can slip past the first check unnoticed).
    """
    if not relative_path or not relative_path.strip():
        raise UnsafeArtifactPathError("Artifact path must not be empty.")

    candidate = Path(relative_path)

    if candidate.is_absolute():
        raise UnsafeArtifactPathError(
            "Artifact path must be relative to the workspace, got an absolute "
            f"path: {relative_path!r}"
        )

    if ".." in candidate.parts:
        raise UnsafeArtifactPathError(
            f"Artifact path must not contain '..' segments: {relative_path!r}"
        )

    resolved = (ARTIFACT_WORKSPACE_ROOT / candidate).resolve()

    if not resolved.is_relative_to(ARTIFACT_WORKSPACE_ROOT):
        raise UnsafeArtifactPathError(
            f"Artifact path resolves outside the approved workspace: {relative_path!r}"
        )

    return resolved
