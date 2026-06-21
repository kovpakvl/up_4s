import pytest

from secureoffice_backend.config import AppConfig, DEFAULT_DATABASE_URL


def test_config_reads_defaults(monkeypatch):
    monkeypatch.delenv("SECUREOFFICE_DATABASE_URL", raising=False)
    monkeypatch.delenv("SECUREOFFICE_PORT", raising=False)

    config = AppConfig.from_env()

    assert config.database_url == DEFAULT_DATABASE_URL
    assert config.port == 8765
    assert config.activation_ttl_days == 3


def test_config_rejects_invalid_port(monkeypatch):
    monkeypatch.setenv("SECUREOFFICE_PORT", "abc")

    with pytest.raises(ValueError):
        AppConfig.from_env()
