"""Daily Challenge widget: today's problem with a difficulty badge.

Small and medium sizes. Shows the real title/difficulty once a
:class:`DashboardSnapshot` is available, and the "Solve" button opens the
real challenge URL in the default browser; falls back to sample data (and
an inert button) beforehand.
"""

from __future__ import annotations

import webbrowser

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.desktop._common import make_icon_badge, make_pill

_SAMPLE_TITLE = "Maximum Subsequence Score"
_SAMPLE_DIFFICULTY = "Medium"


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the daily challenge widget content for the given size."""
    challenge = snapshot.daily_challenge if snapshot is not None else None
    title = challenge.title if challenge is not None else _SAMPLE_TITLE
    difficulty = challenge.difficulty if challenge is not None else _SAMPLE_DIFFICULTY
    url = challenge.url if challenge is not None else None

    if size == WidgetSize.MEDIUM:
        return _render_medium(theme, title, difficulty, url)
    return _render_small(theme, title, difficulty, url)


def _solve_button(theme: Theme, url: str | None, text: str = "Solve") -> QPushButton:
    button = QPushButton(text)
    button.setStyleSheet(
        f"background: {theme.colors.warning}; color: {theme.colors.background};"
        f"border-radius: 8px; padding: 4px 12px; font-size: 10px; font-weight: 700; border: none;"
    )
    if url is not None:
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.clicked.connect(lambda: webbrowser.open(url))
    return button


def _render_small(theme: Theme, title: str, difficulty: str, url: str | None) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    layout.setContentsMargins(12, 12, 12, 12)
    layout.setSpacing(8)

    icon = QLabel("⚡")
    icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
    icon.setStyleSheet("font-size: 26px;")
    layout.addWidget(icon)

    title_label = QLabel(title)
    title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    title_label.setWordWrap(True)
    title_label.setStyleSheet(
        f"font-size: 10px; font-weight: 600; color: {theme.colors.text_primary};"
    )
    layout.addWidget(title_label)

    pill = make_pill(
        difficulty,
        color=theme.colors.warning,
        background="rgba(255, 161, 22, 0.1)",
    )
    layout.addWidget(pill, alignment=Qt.AlignmentFlag.AlignCenter)
    layout.addWidget(_solve_button(theme, url), alignment=Qt.AlignmentFlag.AlignCenter)

    return container


def _render_medium(theme: Theme, title: str, difficulty: str, url: str | None) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(16, 0, 16, 0)
    layout.setSpacing(12)

    layout.addWidget(make_icon_badge("⚡", 48, "rgba(255, 161, 22, 0.1)", radius=16))

    text_column = QVBoxLayout()
    text_column.setSpacing(4)
    label = QLabel("DAILY CHALLENGE")
    label.setStyleSheet(
        f"font-size: 9px; color: {theme.colors.text_secondary}; letter-spacing: 1px;"
    )
    text_column.addWidget(label)

    title_label = QLabel(title)
    title_label.setStyleSheet(
        f"font-size: 13px; font-weight: 600; color: {theme.colors.text_primary};"
    )
    text_column.addWidget(title_label)

    footer_row = QHBoxLayout()
    footer_row.addWidget(
        make_pill(difficulty, color=theme.colors.warning, background="rgba(255, 161, 22, 0.1)")
    )
    footer_row.addWidget(_solve_button(theme, url, "Solve →"))
    footer_row.addStretch()
    text_column.addLayout(footer_row)

    layout.addLayout(text_column, stretch=1)
    return container
