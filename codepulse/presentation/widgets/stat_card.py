"""A small themed card showing a title and an animated numeric value.

Used throughout the dashboard (Phase 5) for things like "Total Solved" or
"Current Streak" -- this widget only knows how to display and animate a
number, it has no idea what the number means.
"""

from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from codepulse.presentation.animations.transitions import animate_value
from codepulse.presentation.themes.theme import Theme


def _default_value_formatter(value: float) -> str:
    return str(round(value))


class StatCard(QWidget):
    """A themed, animated "icon + title + value" card."""

    def __init__(
        self,
        title: str,
        theme: Theme,
        *,
        icon: str = "",
        value_formatter: Callable[[float], str] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._value_formatter = value_formatter or _default_value_formatter
        self._current_value = 0.0

        icon_label = QLabel(icon)
        title_label = QLabel(title)
        title_label.setProperty("role", "secondary")

        self._value_label = QLabel(self._value_formatter(0.0))
        value_font = self._value_label.font()
        value_font.setPointSize(20)
        value_font.setBold(True)
        self._value_label.setFont(value_font)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.addWidget(icon_label)
        header_row.addWidget(title_label)
        header_row.addStretch()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)
        layout.addLayout(header_row)
        layout.addWidget(self._value_label)

        self.apply_theme(theme)

    @property
    def current_value(self) -> float:
        """The currently displayed value (mid-animation if one is running)."""
        return self._current_value

    @property
    def displayed_text(self) -> str:
        """The formatted text currently shown in the value label."""
        return self._value_label.text()

    def apply_theme(self, theme: Theme) -> None:
        """Restyle the card for the given theme."""
        self._theme = theme
        card_radius = max(theme.corner_radius - 6, 6)
        self.setStyleSheet(f"""
            StatCard {{
                background: {theme.colors.surface_alt};
                border: 1px solid {theme.colors.border};
                border-radius: {card_radius}px;
            }}
            """)
        self._value_label.setStyleSheet(f"color: {theme.colors.accent};")

    def set_value(self, new_value: float, *, animate: bool = True) -> None:
        """Update the displayed value, animating the transition by default."""
        if not animate:
            self._current_value = new_value
            self._value_label.setText(self._value_formatter(new_value))
            return

        animate_value(self._current_value, new_value, self._on_animated_value, parent=self)
        self._current_value = new_value

    def _on_animated_value(self, value: float) -> None:
        self._value_label.setText(self._value_formatter(value))
