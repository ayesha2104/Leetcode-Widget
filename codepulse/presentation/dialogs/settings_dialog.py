"""The Settings dialog: everything in :class:`UserPreferences`, editable.

Applies theme changes immediately on save; opacity and Windows-startup
registration are applied by whoever opens the dialog via
:attr:`settings_saved`, since those effects reach beyond this dialog's own
knowledge (other open windows, the OS registry).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
)

from codepulse.domain.interfaces.settings_repository import SettingsRepository
from codepulse.domain.models.preferences import ThemeName, UserPreferences
from codepulse.presentation.themes.theme_manager import ThemeManager
from codepulse.presentation.windows.base_frameless_window import FramelessWindow

_DIALOG_SIZE = (360, 520)
_OPACITY_MIN_PERCENT = 20
_OPACITY_MAX_PERCENT = 100


class SettingsDialog(FramelessWindow):
    """A form for viewing and editing :class:`UserPreferences`."""

    settings_saved = Signal(object)  # UserPreferences
    manage_goals_requested = Signal()

    def __init__(self, repository: SettingsRepository, theme_manager: ThemeManager) -> None:
        super().__init__(theme_manager.current_theme, always_on_top=False, resizable=False)
        self._repository = repository
        self._theme_manager = theme_manager
        self._preferences = repository.load()

        self.setFixedSize(*_DIALOG_SIZE)
        self._build_ui()
        self._populate_from_preferences()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(14)

        title_row = QHBoxLayout()
        title = QLabel("Settings")
        title.setProperty("role", "heading")
        title_row.addWidget(title)
        title_row.addStretch()
        close_button = QPushButton("✕")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)
        title_row.addWidget(close_button)
        root.addLayout(title_row)

        form = QFormLayout()
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

        self._username_edit = QLineEdit()
        self._username_edit.setPlaceholderText("LeetCode username")
        form.addRow("Username", self._username_edit)

        self._theme_combo = QComboBox()
        for theme_name in ThemeName:
            self._theme_combo.addItem(theme_name.value.capitalize(), theme_name.value)
        form.addRow("Theme", self._theme_combo)

        opacity_row = QHBoxLayout()
        self._opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self._opacity_slider.setRange(_OPACITY_MIN_PERCENT, _OPACITY_MAX_PERCENT)
        self._opacity_value_label = QLabel()
        self._opacity_slider.valueChanged.connect(
            lambda value: self._opacity_value_label.setText(f"{value}%")
        )
        opacity_row.addWidget(self._opacity_slider, stretch=1)
        opacity_row.addWidget(self._opacity_value_label)
        form.addRow("Opacity", opacity_row)

        self._refresh_interval_spin = QSpinBox()
        self._refresh_interval_spin.setRange(1, 1440)
        self._refresh_interval_spin.setSuffix(" min")
        form.addRow("Refresh interval", self._refresh_interval_spin)

        self._cache_duration_spin = QSpinBox()
        self._cache_duration_spin.setRange(1, 1440)
        self._cache_duration_spin.setSuffix(" min")
        form.addRow("Cache duration", self._cache_duration_spin)

        self._always_on_top_check = QCheckBox("Always on top")
        form.addRow(self._always_on_top_check)

        self._start_with_windows_check = QCheckBox("Start with Windows")
        form.addRow(self._start_with_windows_check)

        self._animations_check = QCheckBox("Enable animations")
        form.addRow(self._animations_check)

        self._notifications_check = QCheckBox("Enable notifications")
        form.addRow(self._notifications_check)

        root.addLayout(form)

        manage_goals_button = QPushButton("Manage Goals…")
        manage_goals_button.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_goals_button.clicked.connect(self.manage_goals_requested.emit)
        root.addWidget(manage_goals_button)

        root.addStretch()

        button_row = QHBoxLayout()
        button_row.addStretch()
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.close)
        button_row.addWidget(cancel_button)
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._on_save_clicked)
        button_row.addWidget(save_button)
        root.addLayout(button_row)

    def _populate_from_preferences(self) -> None:
        preferences = self._preferences
        self._username_edit.setText(preferences.username or "")
        self._theme_combo.setCurrentText(preferences.theme.value.capitalize())
        self._opacity_slider.setValue(round(preferences.opacity * 100))
        self._refresh_interval_spin.setValue(preferences.refresh_interval_minutes)
        self._cache_duration_spin.setValue(preferences.cache_duration_minutes)
        self._always_on_top_check.setChecked(preferences.always_on_top)
        self._start_with_windows_check.setChecked(preferences.start_with_windows)
        self._animations_check.setChecked(preferences.animations_enabled)
        self._notifications_check.setChecked(preferences.notifications_enabled)

    def _build_preferences_from_form(self) -> UserPreferences:
        username = self._username_edit.text().strip() or None
        return UserPreferences(
            username=username,
            active_provider=self._preferences.active_provider,
            theme=ThemeName(self._theme_combo.currentData()),
            opacity=self._opacity_slider.value() / 100,
            refresh_interval_minutes=self._refresh_interval_spin.value(),
            cache_duration_minutes=self._cache_duration_spin.value(),
            always_on_top=self._always_on_top_check.isChecked(),
            start_with_windows=self._start_with_windows_check.isChecked(),
            animations_enabled=self._animations_check.isChecked(),
            notifications_enabled=self._notifications_check.isChecked(),
        )

    def _on_save_clicked(self) -> None:
        preferences = self._build_preferences_from_form()
        self._repository.save(preferences)
        self._theme_manager.set_theme(preferences.theme.value)
        self.settings_saved.emit(preferences)
        self.close()
