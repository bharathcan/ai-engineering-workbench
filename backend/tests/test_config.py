from app.core.config import Settings


def test_settings_load_with_defaults_and_no_external_services(monkeypatch):
    # conftest.py sets DATABASE_URL process-wide to isolate the test database
    # (see tests/conftest.py) — unset it here so this test still verifies the
    # real default-with-nothing-configured behavior it's named for.
    monkeypatch.delenv("DATABASE_URL", raising=False)
    settings = Settings(_env_file=None)
    assert settings.app_env == "development"
    assert settings.app_host == "0.0.0.0"
    assert settings.app_port == 8000
    assert settings.database_url is None
    assert settings.redis_url is None
    assert settings.ai_api_key is None


def test_settings_read_from_environment(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("APP_PORT", "9000")
    settings = Settings(_env_file=None)
    assert settings.app_env == "production"
    assert settings.app_port == 9000
