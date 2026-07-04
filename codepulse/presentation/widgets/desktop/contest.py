"""Contest widget: upcoming contest with a live countdown.

Medium and large sizes. Uses a representative sample contest and a
fixed sample countdown duration -- LeetCode's upcoming-contest schedule
isn't fetched by any provider yet (only past contest *ranking* is, via
:meth:`ProviderInterface.get_contest_info`), so this is visual-only for
now. The "Register" button is intentionally inert pending that data.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.domain.models.widget import WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.desktop._common import make_icon_badge

_SAMPLE_CONTEST_NAME = "Weekly Contest 416"
_SAMPLE_CONTEST_DATE = "Sun, Jul 6 · 10:30 AM IST"
_SAMPLE_SECONDS_REMAINING = 4 * 3600 + 23 * 60 + 17
_SAMPLE_CONTESTS_TO_GO = 3


class _CountdownLabel(QLabel):
    """A label that ticks a countdown down once per second until it reaches zero."""

    def __init__(self, seconds_remaining: int, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._seconds_remaining = seconds_remaining
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._timer.start()
        self._render()

    def _tick(self) -> None:
        if self._seconds_remaining <= 0:
            self._timer.stop()
            return
        self._seconds_remaining -= 1
        self._render()

    def _render(self) -> None:
        hours, remainder = divmod(max(self._seconds_remaining, 0), 3600)
        minutes, seconds = divmod(remainder, 60)
        self.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")


def render(size: WidgetSize, theme: Theme, snapshot: DashboardSnapshot | None = None) -> QWidget:
    """Build the contest widget content for the given size.

    ``snapshot`` is accepted for interface uniformity but ignored -- no
    provider exposes upcoming-contest schedule data yet.
    """
    if size == WidgetSize.LARGE:
        return _render_large(theme)
    return _render_medium(theme)


def _register_button(theme: Theme) -> QPushButton:
    button = QPushButton("\U0001f44b Register")
    button.setStyleSheet(
        f"background: {theme.colors.surface_alt}; color: {theme.colors.text_primary};"
        f"border-radius: 14px; padding: 6px 14px; font-size: 11px; font-weight: 600; border: none;"
    )
    return button


def _render_medium(theme: Theme) -> QWidget:
    container = QWidget()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    left = QFrame()
    left.setStyleSheet(f"border-right: 1px solid {theme.colors.border};")
    left_layout = QVBoxLayout(left)
    left_layout.setContentsMargins(14, 12, 14, 12)
    left_layout.addWidget(
        make_icon_badge("\U0001f3c6", 36, f"{theme.colors.accent_secondary}", radius=10)
    )
    upcoming = QLabel("Upcoming")
    upcoming.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    left_layout.addWidget(upcoming)
    title = QLabel(_SAMPLE_CONTEST_NAME)
    title.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {theme.colors.text_primary};")
    title.setWordWrap(True)
    left_layout.addWidget(title)
    left_layout.addStretch()
    left_layout.addWidget(_register_button(theme))
    layout.addWidget(left, stretch=1)

    right = QVBoxLayout()
    right.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right.setContentsMargins(14, 12, 14, 12)
    right.setSpacing(2)
    trophy = QLabel("\U0001f3c6")
    trophy.setAlignment(Qt.AlignmentFlag.AlignCenter)
    trophy.setStyleSheet("font-size: 26px;")
    right.addWidget(trophy)
    hint = QLabel(f"Attend {_SAMPLE_CONTESTS_TO_GO} more\ncontests")
    hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
    hint.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    right.addWidget(hint)
    countdown = _CountdownLabel(_SAMPLE_SECONDS_REMAINING)
    countdown.setAlignment(Qt.AlignmentFlag.AlignCenter)
    countdown.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {theme.colors.warning};")
    right.addWidget(countdown)
    right_widget = QWidget()
    right_widget.setLayout(right)
    layout.addWidget(right_widget, stretch=1)

    return container


def _render_large(theme: Theme) -> QWidget:
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(16, 14, 16, 14)
    layout.setSpacing(12)

    header = QHBoxLayout()
    header.addWidget(make_icon_badge("\U0001f3c6", 44, theme.colors.accent_secondary, radius=14))
    text_column = QVBoxLayout()
    text_column.setSpacing(1)
    upcoming = QLabel("UPCOMING")
    upcoming.setStyleSheet(
        f"font-size: 9px; color: {theme.colors.text_secondary}; letter-spacing: 1px;"
    )
    text_column.addWidget(upcoming)
    title = QLabel(_SAMPLE_CONTEST_NAME)
    title.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {theme.colors.text_primary};")
    text_column.addWidget(title)
    date_label = QLabel(_SAMPLE_CONTEST_DATE)
    date_label.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
    text_column.addWidget(date_label)
    header.addLayout(text_column)
    header.addStretch()
    layout.addLayout(header)

    countdown_box = QFrame()
    countdown_box.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    countdown_box.setStyleSheet(
        "background: rgba(255, 161, 22, 0.06); border: 1px solid rgba(255, 161, 22, 0.15);"
        "border-radius: 14px;"
    )
    countdown_layout = QHBoxLayout(countdown_box)
    countdown_layout.setContentsMargins(14, 10, 14, 10)
    countdown_text_column = QVBoxLayout()
    starts_in = QLabel("STARTS IN")
    starts_in.setStyleSheet(
        f"font-size: 9px; color: {theme.colors.text_secondary}; letter-spacing: 1px;"
    )
    countdown_text_column.addWidget(starts_in)
    countdown = _CountdownLabel(_SAMPLE_SECONDS_REMAINING)
    countdown.setStyleSheet(f"font-size: 22px; font-weight: 800; color: {theme.colors.warning};")
    countdown_text_column.addWidget(countdown)
    countdown_layout.addLayout(countdown_text_column)
    countdown_layout.addStretch()

    register = QPushButton("Register")
    register.setStyleSheet(
        f"background: {theme.colors.warning}; color: {theme.colors.background};"
        f"border-radius: 10px; padding: 8px 18px; font-size: 12px; font-weight: 700; border: none;"
    )
    countdown_layout.addWidget(register)
    layout.addWidget(countdown_box)

    footer = QFrame()
    footer.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    footer.setStyleSheet(f"background: {theme.colors.surface_alt}; border-radius: 12px;")
    footer_layout = QHBoxLayout(footer)
    footer_layout.setContentsMargins(12, 8, 12, 8)
    footer_trophy = QLabel("\U0001f3c6")
    footer_trophy.setStyleSheet(f"font-size: 16px; color: {theme.colors.warning};")
    footer_layout.addWidget(footer_trophy)
    footer_text = QLabel(f"Attend {_SAMPLE_CONTESTS_TO_GO} more contests for a badge")
    footer_text.setStyleSheet(f"font-size: 11px; color: {theme.colors.text_secondary};")
    footer_layout.addWidget(footer_text, stretch=1)
    layout.addWidget(footer)

    return container
