"""Runtime configuration for the DOCUPRO conversion service.

All values are supplied through environment variables so that nothing
secret or deployment specific is baked into the image or the repository.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _int(name: str, default: int, minimum: int = 0) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return max(minimum, value)


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _path(name: str, default: str) -> Path:
    return Path(os.environ.get(name, default)).expanduser().resolve()


@dataclass(frozen=True)
class Settings:
    """Immutable settings object, built once per process."""

    data_dir: Path = field(default_factory=lambda: _path("DOCUPRO_DATA_DIR", "/tmp/docupro"))
    web_dir: Path = field(default_factory=lambda: _path("DOCUPRO_WEB_DIR", ""))

    # Upload policy
    max_upload_bytes: int = field(default_factory=lambda: _int("DOCUPRO_MAX_UPLOAD_MB", 50) * 1024 * 1024)
    max_job_bytes: int = field(default_factory=lambda: _int("DOCUPRO_MAX_JOB_MB", 200) * 1024 * 1024)
    max_files_per_job: int = field(default_factory=lambda: _int("DOCUPRO_MAX_FILES", 20, 1))
    max_pages: int = field(default_factory=lambda: _int("DOCUPRO_MAX_PAGES", 500, 1))
    max_pixels: int = field(default_factory=lambda: _int("DOCUPRO_MAX_PIXELS", 80_000_000, 1_000_000))
    max_ooxml_entries: int = field(default_factory=lambda: _int("DOCUPRO_MAX_OOXML_ENTRIES", 5_000, 10))
    max_ooxml_uncompressed: int = field(default_factory=lambda: _int("DOCUPRO_MAX_OOXML_MB", 300, 10) * 1024 * 1024)

    # Retention / lifecycle
    retention_minutes: int = field(default_factory=lambda: _int("DOCUPRO_RETENTION_MINUTES", 30, 1))
    download_window_minutes: int = field(default_factory=lambda: _int("DOCUPRO_DOWNLOAD_WINDOW_MINUTES", 30, 1))
    sweep_interval_seconds: int = field(default_factory=lambda: _int("DOCUPRO_SWEEP_SECONDS", 30, 5))
    max_retained_jobs: int = field(default_factory=lambda: _int("DOCUPRO_MAX_RETAINED_JOBS", 200, 10))
    # Seconds kept after every artifact has been downloaded at least once.
    # 0 keeps the full retention window.
    delete_after_download_seconds: int = field(
        default_factory=lambda: _int("DOCUPRO_DELETE_AFTER_DOWNLOAD_SECONDS", 120, 0)
    )

    # Execution
    conversion_timeout: int = field(default_factory=lambda: _int("DOCUPRO_CONVERSION_TIMEOUT", 240, 10))
    max_concurrent_jobs: int = field(default_factory=lambda: _int("DOCUPRO_MAX_CONCURRENCY", 2, 1))
    max_queue: int = field(default_factory=lambda: _int("DOCUPRO_MAX_QUEUE", 40, 1))

    # Abuse protection
    rate_limit_per_minute: int = field(default_factory=lambda: _int("DOCUPRO_RATE_LIMIT", 40, 1))
    rate_limit_burst: int = field(default_factory=lambda: _int("DOCUPRO_RATE_BURST", 20, 1))
    trust_proxy_headers: bool = field(default_factory=lambda: _bool("DOCUPRO_TRUST_PROXY", True))

    # HTTP
    cors_origins: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            o.strip() for o in os.environ.get("DOCUPRO_CORS_ORIGINS", "").split(",") if o.strip()
        )
    )
    log_level: str = field(default_factory=lambda: os.environ.get("DOCUPRO_LOG_LEVEL", "INFO").upper())
    version: str = "1.0.0"

    @property
    def jobs_dir(self) -> Path:
        return self.data_dir / "jobs"

    @property
    def tmp_dir(self) -> Path:
        return self.data_dir / "tmp"

    def ensure_dirs(self) -> None:
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.jobs_dir.chmod(0o700)
            self.tmp_dir.chmod(0o700)
        except OSError:  # pragma: no cover - best effort on odd filesystems
            pass


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
        _settings.ensure_dirs()
    return _settings


def reset_settings() -> None:
    """Test helper: drop the cached settings so env changes are picked up."""
    global _settings
    _settings = None
