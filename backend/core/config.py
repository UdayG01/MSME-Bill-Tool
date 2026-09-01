import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = BACKEND_DIR / "db" / "msme_billing.db"
load_dotenv(BACKEND_DIR.parent / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _database_url(value: str | None) -> str:
    if not value:
        return f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}"
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+psycopg://", 1)
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+psycopg://", 1)
    if value.startswith("mysql://"):
        return value.replace("mysql://", "mysql+pymysql://", 1)
    return value


@dataclass(frozen=True)
class Settings:
    app_env: str
    database_url: str
    migration_database_url: str
    frontend_origins: tuple[str, ...]
    session_cookie_secure: bool
    session_cookie_samesite: str
    session_ttl_seconds: int
    log_level: str
    media_storage_path: str
    media_max_logo_bytes: int
    media_max_signature_bytes: int

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"


@lru_cache
def get_settings() -> Settings:
    database_url = _database_url(os.getenv("DATABASE_URL"))
    migration_url = _database_url(os.getenv("MIGRATION_DATABASE_URL") or database_url)
    origins = tuple(
        item.strip().rstrip("/")
        for item in os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(",")
        if item.strip()
    )
    cookie_samesite = os.getenv("SESSION_COOKIE_SAMESITE", "lax").strip().lower()
    if cookie_samesite not in {"lax", "strict", "none"}:
        raise RuntimeError("SESSION_COOKIE_SAMESITE must be lax, strict, or none")
    settings = Settings(
        app_env=os.getenv("APP_ENV", "development"),
        database_url=database_url,
        migration_database_url=migration_url,
        frontend_origins=origins,
        session_cookie_secure=_as_bool(os.getenv("SESSION_COOKIE_SECURE")),
        session_cookie_samesite=cookie_samesite,
        session_ttl_seconds=int(os.getenv("SESSION_TTL_SECONDS", "28800")),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        media_storage_path=os.getenv("MEDIA_STORAGE_PATH", str(BACKEND_DIR / "media")),
        media_max_logo_bytes=int(os.getenv("MEDIA_MAX_LOGO_BYTES", "2097152")),
        media_max_signature_bytes=int(os.getenv("MEDIA_MAX_SIGNATURE_BYTES", "1048576")),
    )
    if settings.is_production:
        if not os.getenv("DATABASE_URL"):
            raise RuntimeError("DATABASE_URL is required when APP_ENV=production")
        if not settings.frontend_origins or any("localhost" in origin for origin in settings.frontend_origins):
            raise RuntimeError("FRONTEND_ORIGINS must contain the deployed frontend URL in production")
        if not settings.session_cookie_secure:
            raise RuntimeError("SESSION_COOKIE_SECURE must be true in production")
    return settings
