"""User-editable application preferences.

Distinct from :class:`codepulse.infrastructure.config.settings.AppSettings`,
which holds developer/ops-facing configuration (log level, data directory).
``UserPreferences`` holds everything a user can change through the Settings
dialog and is persisted by a :class:`~codepulse.domain.interfaces.settings_repository.SettingsRepository`.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ThemeName(StrEnum):
    """Identifiers for the built-in presentation themes."""

    DARK = "dark"
    LIGHT = "light"
    GLASS = "glass"
    LEETCODE = "leetcode"
    CYBERPUNK = "cyberpunk"
    MINIMAL = "minimal"


class UserPreferences(BaseModel):
    """Persisted, user-editable settings.

    All fields have safe defaults so a fresh install renders a usable
    widget before the user opens Settings for the first time.
    """

    username: str | None = None
    active_provider: str = "leetcode"
    theme: ThemeName = ThemeName.DARK
    opacity: float = Field(default=0.95, ge=0.2, le=1.0)
    refresh_interval_minutes: int = Field(default=15, ge=1, le=1440)
    cache_duration_minutes: int = Field(default=30, ge=1, le=1440)
    always_on_top: bool = True
    start_with_windows: bool = False
    animations_enabled: bool = True
    notifications_enabled: bool = True
