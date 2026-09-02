import os
from pathlib import Path

# Point the app at an isolated SQLite file before app.core.config/database are
# ever imported, so tests never touch the developer's real workbench.db.
_TEST_DB_PATH = Path(__file__).parent / "test_workbench.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB_PATH}"
if _TEST_DB_PATH.exists():
    _TEST_DB_PATH.unlink()

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.api.deps import get_ai_provider_factory  # noqa: E402
from app.core.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.utils import safe_path  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Redirect artifact writes to an isolated temp dir for the duration of
    # each test — otherwise resolve_artifact_path() would write real files
    # into this repo's actual generated/ directory on every test run.
    monkeypatch.setattr(safe_path, "ARTIFACT_WORKSPACE_ROOT", tmp_path)

    Base.metadata.create_all(bind=engine)
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_ai_provider_factory, None)


@pytest.fixture(scope="session", autouse=True)
def _cleanup_test_db():
    yield
    if _TEST_DB_PATH.exists():
        _TEST_DB_PATH.unlink()
