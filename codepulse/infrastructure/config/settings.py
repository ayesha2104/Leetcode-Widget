"""Developer/ops-facing application configuration.

Loaded once at startup from environment variables (see ``.env.example``),
falling back to sane defaults. This is distinct from
:class:`codepulse.domain.models.preferences.UserPreferences`, which holds
settings the *user* changes at runtime through the UI.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_APP_DIR_NAME = "CodePulse"


class AppSettings(BaseSettings):
    """Environment-driven configuration, prefixed with ``CODEPULSE_``."""

    model_config = SettingsConfigDict(
        env_prefix="CODEPULSE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = "INFO"
    data_dir: Path | None = None
    http_timeout: float = Field(default=10.0, gt=0)

    @property
    def resolved_data_dir(self) -> Path:
        """The directory CodePulse stores its database, cache, and logs in.

        Defaults to ``%LOCALAPPDATA%\\CodePulse`` on Windows, falling back to
        ``~/.codepulse`` on other platforms (useful for running tests on CI).
        """
        if self.data_dir is not None:
            return self.data_dir

        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            return Path(local_app_data) / _APP_DIR_NAME

        return Path.home() / ".codepulse"

    @property
    def database_path(self) -> Path:
        """Path to the SQLite database file."""
        return self.resolved_data_dir / "codepulse.db"

    @property
    def settings_file_path(self) -> Path:
        """Path to the user preferences JSON file."""
        return self.resolved_data_dir / "settings.json"

    @property
    def desktop_layout_file_path(self) -> Path:
        """Path to the placed-desktop-widgets JSON file."""
        return self.resolved_data_dir / "desktop_layout.json"

    @property
    def goals_file_path(self) -> Path:
        """Path to the user-defined goals JSON file."""
        return self.resolved_data_dir / "goals.json"

    @property
    def notification_state_file_path(self) -> Path:
        """Path to the notification de-duplication state JSON file."""
        return self.resolved_data_dir / "notification_state.json"

    @property
    def log_dir(self) -> Path:
        """Directory rotating log files are written to."""
        return self.resolved_data_dir / "logs"


@lru_cache(maxsize=1)
def get_app_settings() -> AppSettings:
    """Return the process-wide :class:`AppSettings` singleton."""
    return AppSettings()
