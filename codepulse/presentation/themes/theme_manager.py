"""Loads theme JSON files and broadcasts theme changes to the UI.

The main window and every themed widget connect to
:attr:`ThemeManager.theme_changed` once, at construction time, rather than
polling -- switching themes is then a single ``set_theme`` call away from
updating the entire UI.
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from PySide6.QtCore import QObject, Signal

from codepulse.domain.exceptions import ConfigurationError
from codepulse.presentation.themes.theme import Theme
from codepulse.utils.resource_paths import get_assets_dir

DEFAULT_THEME_NAME = "dark"


def _themes_dir() -> Path:
    return get_assets_dir() / "themes"


def list_available_themes() -> list[str]:
    """Return the names of every theme JSON file found on disk."""
    return sorted(path.stem for path in _themes_dir().glob("*.json"))


def load_theme(name: str) -> Theme:
    """Load and validate a single theme by name (without the ``.json`` suffix)."""
    path = _themes_dir() / f"{name}.json"
    if not path.exists():
        raise ConfigurationError(f"Unknown theme {name!r}: no file at {path}")

    try:
        return Theme.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(f"Failed to load theme {name!r} from {path}") from exc


def build_stylesheet(theme: Theme) -> str:
    """Generate a QSS stylesheet for standard Qt widgets from theme tokens.

    Custom-painted widgets (the main window backdrop, ``ProgressRing``) read
    :class:`Theme` colors directly instead of relying on QSS.
    """
    c = theme.colors
    return f"""
        QWidget {{
            background: transparent;
            color: {c.text_primary};
            font-family: "Segoe UI", sans-serif;
        }}
        QLabel[role="secondary"] {{
            color: {c.text_secondary};
        }}
        QLabel[role="heading"] {{
            color: {c.text_primary};
            font-weight: 600;
        }}
        QPushButton, QToolButton {{
            background: {c.surface_alt};
            border: 1px solid {c.border};
            border-radius: 8px;
            padding: 6px 12px;
            color: {c.text_primary};
        }}
        QPushButton:hover, QToolButton:hover {{
            background: {c.accent};
            color: {c.background};
            border-color: {c.accent};
        }}
        QPushButton:pressed, QToolButton:pressed {{
            background: {c.accent_secondary};
            border-color: {c.accent_secondary};
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
        }}
        QScrollBar::handle:vertical {{
            background: {c.border};
            border-radius: 4px;
            min-height: 24px;
        }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
    """


class ThemeManager(QObject):
    """Owns the active :class:`Theme` and notifies listeners when it changes."""

    theme_changed = Signal(Theme)

    def __init__(self, initial_theme_name: str = DEFAULT_THEME_NAME) -> None:
        super().__init__()
        self._current_theme = load_theme(initial_theme_name)

    @property
    def current_theme(self) -> Theme:
        """The currently active theme."""
        return self._current_theme

    def set_theme(self, name: str) -> None:
        """Load ``name`` and emit :attr:`theme_changed` if it differs from the current theme."""
        if name == self._current_theme.name:
            return

        theme = load_theme(name)
        self._current_theme = theme
        logger.info("Theme changed to {}", theme.name)
        self.theme_changed.emit(theme)

    def cycle_theme(self) -> None:
        """Switch to the next theme in alphabetical order, wrapping around."""
        names = list_available_themes()
        current_index = names.index(self._current_theme.name)
        next_name = names[(current_index + 1) % len(names)]
        self.set_theme(next_name)
