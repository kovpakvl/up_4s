from dataclasses import dataclass
from os import getenv


DEFAULT_DATABASE_URL = "postgresql://secureoffice:secureoffice@localhost:5432/secureoffice"


@dataclass(frozen=True)
class AppConfig:
    database_url: str
    host: str = "127.0.0.1"
    port: int = 8765
    session_ttl_hours: int = 12
    activation_ttl_days: int = 3

    @classmethod
    def from_env(cls) -> "AppConfig":
        return cls(
            database_url=getenv("SECUREOFFICE_DATABASE_URL", DEFAULT_DATABASE_URL),
            host=getenv("SECUREOFFICE_HOST", "127.0.0.1"),
            port=_env_int("SECUREOFFICE_PORT", 8765),
            session_ttl_hours=_env_int("SECUREOFFICE_SESSION_TTL_HOURS", 12),
            activation_ttl_days=_env_int("SECUREOFFICE_ACTIVATION_TTL_DAYS", 3),
        )


def _env_int(name: str, default: int) -> int:
    value = getenv(name)
    if value is None or value.strip() == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer.") from exc
    if parsed <= 0:
        raise ValueError(f"{name} must be positive.")
    return parsed
