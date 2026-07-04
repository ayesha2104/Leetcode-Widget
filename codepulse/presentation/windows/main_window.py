"""CodePulse's control panel: a small launcher for the desktop widget system.

Rather than hosting a dashboard itself, this window is a compact utility
panel -- theme cycling, a system tray icon, and the entry point to the
widget picker gallery. The actual LeetCode data lives in independent
floating widgets managed by :class:`DesktopWidgetManager`.
"""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QPushButton,
    QSystemTrayIcon,
    QVBoxLayout,
)

from codepulse.application.services.goal_service import GoalService
from codepulse.domain.interfaces.settings_repository import SettingsRepository
from codepulse.domain.models.preferences import UserPreferences
from codepulse.infrastructure.os.windows_startup import set_start_with_windows
from codepulse.presentation.desktop_widget_manager import DesktopWidgetManager
from codepulse.presentation.dialogs.goals_dialog import GoalsDialog
from codepulse.presentation.dialogs.settings_dialog import SettingsDialog
from codepulse.presentation.dialogs.widget_picker_dialog import WidgetPickerDialog
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.themes.theme_manager import ThemeManager, build_stylesheet
from codepulse.presentation.windows.base_frameless_window import FramelessWindow
from codepulse.utils.color import parse_color

_TRAY_ICON_SIZE = 32
_PANEL_SIZE = QSize(280, 190)

# An EKG-style heartbeat trace, as fractions of the icon's size: flat, a
# small dip, a tall spike, a deep drop, flat again -- the same "pulse"
# shape used by scripts/generate_icon.py for the packaged .ico, so the tray
# icon and the taskbar/file icon read as the same mark.
_PULSE_TRACE_POINTS = (
    (0.16, 0.50),
    (0.34, 0.50),
    (0.42, 0.34),
    (0.50, 0.66),
    (0.58, 0.14),
    (0.66, 0.72),
    (0.74, 0.50),
    (0.86, 0.50),
)


_CHROME_ICON_SIZE = 16


def _draw_theme_icon(color: QColor) -> QIcon:
    """A half-filled circle (light/dark split), representing theme switching."""
    size = _CHROME_ICON_SIZE
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color)
    pen.setWidthF(1.3)
    painter.setPen(pen)
    margin = 1
    painter.setBrush(color)
    painter.drawPie(margin, margin, size - 2 * margin, size - 2 * margin, 90 * 16, 180 * 16)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(margin, margin, size - 2 * margin, size - 2 * margin)
    painter.end()

    return QIcon(pixmap)


def _draw_settings_icon(color: QColor) -> QIcon:
    """Three horizontal slider rows, the common "settings/preferences" glyph."""
    size = _CHROME_ICON_SIZE
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color)
    pen.setWidthF(1.3)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)

    rows = (4, 8, 12)
    knob_x = (10.0, 5.0, 9.0)
    for y in rows:
        painter.drawLine(QPointF(2, y), QPointF(size - 2, y))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color)
    for y, knob in zip(rows, knob_x, strict=True):
        painter.drawEllipse(QPointF(knob, y), 1.6, 1.6)
    painter.end()

    return QIcon(pixmap)


def _draw_close_icon(color: QColor) -> QIcon:
    """A simple X, drawn rather than relying on a font glyph."""
    size = _CHROME_ICON_SIZE
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    pen = QPen(color)
    pen.setWidthF(1.6)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    margin = 4
    painter.drawLine(margin, margin, size - margin, size - margin)
    painter.drawLine(size - margin, margin, margin, size - margin)
    painter.end()

    return QIcon(pixmap)


def _build_pulse_icon(color: QColor) -> QIcon:
    """Draw the CodePulse "pulse" glyph (a filled circle with an EKG trace) for the tray/window icon."""
    pixmap = QPixmap(_TRAY_ICON_SIZE, _TRAY_ICON_SIZE)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(Qt.PenStyle.NoPen)
    margin = 2
    painter.drawEllipse(margin, margin, _TRAY_ICON_SIZE - 2 * margin, _TRAY_ICON_SIZE - 2 * margin)

    trace = QPainterPath()
    size = _TRAY_ICON_SIZE
    start_x, start_y = _PULSE_TRACE_POINTS[0]
    trace.moveTo(QPointF(start_x * size, start_y * size))
    for x, y in _PULSE_TRACE_POINTS[1:]:
        trace.lineTo(QPointF(x * size, y * size))

    pen = QPen(Qt.GlobalColor.white)
    pen.setWidthF(size * 0.09)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.strokePath(trace, pen)
    painter.end()

    return QIcon(pixmap)


class MainWindow(FramelessWindow):
    """The always-on-top control panel for managing desktop widgets."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        widget_manager: DesktopWidgetManager,
        settings_repository: SettingsRepository,
        goal_service: GoalService,
        *,
        always_on_top: bool = True,
    ) -> None:
        super().__init__(theme_manager.current_theme, always_on_top=always_on_top, resizable=False)
        self._theme_manager = theme_manager
        self._widget_manager = widget_manager
        self._settings_repository = settings_repository
        self._goal_service = goal_service
        self._tray_icon: QSystemTrayIcon | None = None

        self.setFixedSize(_PANEL_SIZE)
        self._build_chrome()
        self._build_tray_icon()
        self._theme_manager.theme_changed.connect(self._on_theme_changed)
        self._widget_manager.widget_count_changed.connect(self._on_widget_count_changed)
        self._apply_stylesheet()
        self._on_widget_count_changed(self._widget_manager.widget_count())

    def _build_chrome(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 14)
        root_layout.setSpacing(10)

        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("CodePulse")
        title_label.setProperty("role", "heading")

        self._theme_button = self._make_chrome_button("Cycle theme")
        self._theme_button.clicked.connect(self._theme_manager.cycle_theme)

        self._settings_button = self._make_chrome_button("Settings")
        self._settings_button.clicked.connect(self._on_settings_clicked)

        self._hide_button = self._make_chrome_button("Hide to tray")
        self._hide_button.clicked.connect(self.hide)

        self._refresh_chrome_icons()

        title_bar.addWidget(title_label)
        title_bar.addStretch()
        for button in (self._theme_button, self._settings_button, self._hide_button):
            title_bar.addWidget(button)
        root_layout.addLayout(title_bar)

        root_layout.addStretch()

        self._add_widget_button = QPushButton("+ Add Widget")
        self._add_widget_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_widget_button.clicked.connect(self._on_add_widget_clicked)
        root_layout.addWidget(self._add_widget_button)

        self._count_label = QLabel()
        self._count_label.setProperty("role", "secondary")
        self._count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root_layout.addWidget(self._count_label)

    @staticmethod
    def _make_chrome_button(tooltip: str) -> QPushButton:
        button = QPushButton()
        button.setToolTip(tooltip)
        button.setFixedSize(28, 28)
        button.setIconSize(QSize(_CHROME_ICON_SIZE, _CHROME_ICON_SIZE))
        return button

    def _refresh_chrome_icons(self) -> None:
        """(Re)draw the title-bar icons in the current theme's text color.

        Drawn with QPainter rather than rendered from a Unicode glyph --
        the app-wide stylesheet pins the font to "Segoe UI", which has no
        automatic per-glyph fallback for symbols like the emoji/dingbats
        previously used here, so they rendered as unreadable placeholder
        marks instead of an icon.
        """
        color = parse_color(self._theme_manager.current_theme.colors.text_primary)
        self._theme_button.setIcon(_draw_theme_icon(color))
        self._settings_button.setIcon(_draw_settings_icon(color))
        self._hide_button.setIcon(_draw_close_icon(color))

    def _on_add_widget_clicked(self) -> None:
        picker = WidgetPickerDialog(self._theme_manager.current_theme)
        picker.widget_added.connect(self._widget_manager.add_widget)
        picker.show()

    def _on_settings_clicked(self) -> None:
        dialog = SettingsDialog(self._settings_repository, self._theme_manager)
        dialog.settings_saved.connect(self._on_settings_saved)
        dialog.manage_goals_requested.connect(self._on_manage_goals_requested)
        dialog.show()

    def _on_settings_saved(self, preferences: UserPreferences) -> None:
        self.set_opacity(preferences.opacity)
        self._widget_manager.set_opacity(preferences.opacity)
        self._widget_manager.set_username(preferences.username)
        self._widget_manager.set_refresh_interval_minutes(preferences.refresh_interval_minutes)
        self._widget_manager.set_notifications_enabled(preferences.notifications_enabled)
        set_start_with_windows(preferences.start_with_windows)

    def _on_manage_goals_requested(self) -> None:
        dialog = GoalsDialog(
            self._goal_service,
            self._theme_manager.current_theme,
            self._widget_manager.get_snapshot(),
        )
        dialog.goals_changed.connect(self._widget_manager.refresh_goals)
        dialog.show()

    def _on_widget_count_changed(self, count: int) -> None:
        self._count_label.setText(f"{count} widget{'s' if count != 1 else ''} active")

    def _build_tray_icon(self) -> None:
        icon = _build_pulse_icon(parse_color(self._theme_manager.current_theme.colors.accent))
        self.setWindowIcon(icon)

        tray_icon = QSystemTrayIcon(icon, self)
        tray_icon.setToolTip("CodePulse")

        menu = QMenu()
        show_action = menu.addAction("Show CodePulse")
        show_action.triggered.connect(self._restore_from_tray)
        add_widget_action = menu.addAction("Add Widget…")
        add_widget_action.triggered.connect(self._on_add_widget_clicked)
        settings_action = menu.addAction("Settings…")
        settings_action.triggered.connect(self._on_settings_clicked)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self._on_exit_requested)
        tray_icon.setContextMenu(menu)
        tray_icon.activated.connect(self._on_tray_activated)
        tray_icon.show()

        self._tray_icon = tray_icon

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self._restore_from_tray()

    def _restore_from_tray(self) -> None:
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_exit_requested(self) -> None:
        QApplication.quit()

    def _on_theme_changed(self, theme: Theme) -> None:
        self.apply_theme(theme)
        self._apply_stylesheet()
        self._refresh_chrome_icons()
        if self._tray_icon is not None:
            icon = _build_pulse_icon(parse_color(theme.colors.accent))
            self.setWindowIcon(icon)
            self._tray_icon.setIcon(icon)

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet(build_stylesheet(self._theme_manager.current_theme))
