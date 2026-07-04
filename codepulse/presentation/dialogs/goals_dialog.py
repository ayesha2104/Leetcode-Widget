"""The Goals management dialog: add, review, and remove solving goals.

Editing is add/remove only -- there is no in-place "edit", since removing
and re-adding a goal is equally fast and keeps the UI (and this dialog)
simpler. Emits :attr:`goals_changed` whenever the goal list changes so the
caller (the desktop widget manager) can recompute progress for any open
Goals widgets.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from codepulse.application.dto.dashboard_snapshot import DashboardSnapshot
from codepulse.application.dto.goal_progress import GoalProgress
from codepulse.application.services.goal_service import GoalService
from codepulse.domain.models.goal import GoalMetric
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.windows.base_frameless_window import FramelessWindow

_DIALOG_SIZE = (340, 460)
_METRIC_LABELS: dict[GoalMetric, str] = {
    GoalMetric.TOTAL_SOLVED: "Problems Solved",
    GoalMetric.HARD_SOLVED: "Hard Problems Solved",
    GoalMetric.STREAK: "Day Streak",
    GoalMetric.RATING: "Contest Rating",
}


class GoalsDialog(FramelessWindow):
    """A form for adding, reviewing, and removing user-defined goals."""

    goals_changed = Signal()

    def __init__(
        self,
        service: GoalService,
        theme: Theme,
        snapshot: DashboardSnapshot | None = None,
    ) -> None:
        super().__init__(theme, always_on_top=False, resizable=False)
        self._service = service
        self._snapshot = snapshot
        self._theme = theme

        self.setFixedSize(*_DIALOG_SIZE)
        self._build_ui()
        self._refresh_goal_list()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        title_row = QHBoxLayout()
        title = QLabel("Goals")
        title.setProperty("role", "heading")
        title_row.addWidget(title)
        title_row.addStretch()
        close_button = QPushButton("✕")
        close_button.setFixedSize(22, 22)
        close_button.clicked.connect(self.close)
        title_row.addWidget(close_button)
        root.addLayout(title_row)

        self._list_container = QVBoxLayout()
        self._list_container.setSpacing(8)
        list_widget = QWidget()
        list_widget.setLayout(self._list_container)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_area.viewport().setStyleSheet("background: transparent;")
        scroll_area.setWidget(list_widget)
        root.addWidget(scroll_area, stretch=1)

        root.addWidget(self._build_add_form())

    def _build_add_form(self) -> QWidget:
        form = QFrame()
        form.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        form.setStyleSheet(f"background: {self._theme.colors.surface_alt}; border-radius: 12px;")
        layout = QVBoxLayout(form)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        self._metric_combo = QComboBox()
        for metric, label in _METRIC_LABELS.items():
            self._metric_combo.addItem(label, metric.value)
        layout.addWidget(self._metric_combo)

        self._target_spin = QSpinBox()
        self._target_spin.setRange(1, 1_000_000)
        self._target_spin.setValue(100)
        layout.addWidget(self._target_spin)

        add_button = QPushButton("+ Add Goal")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet(
            f"background: {self._theme.colors.accent}; color: {self._theme.colors.background};"
            f"border-radius: 8px; padding: 8px; font-weight: 700; border: none;"
        )
        add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(add_button)

        return form

    def _on_add_clicked(self) -> None:
        metric = GoalMetric(self._metric_combo.currentData())
        target = self._target_spin.value()
        self._service.add_goal(metric, target)
        self._refresh_goal_list()
        self.goals_changed.emit()

    def _on_remove_clicked(self, uid: str) -> None:
        self._service.remove_goal(uid)
        self._refresh_goal_list()
        self.goals_changed.emit()

    def _refresh_goal_list(self) -> None:
        while self._list_container.count():
            item = self._list_container.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

        goals = self._service.list_goals()
        if not goals:
            empty_label = QLabel("No goals yet -- add one below.")
            empty_label.setStyleSheet(
                f"color: {self._theme.colors.text_secondary}; font-size: 11px;"
            )
            self._list_container.addWidget(empty_label)

        for goal in goals:
            progress = self._service.compute_progress(goal, self._snapshot)
            self._list_container.addWidget(self._build_goal_row(progress.goal.uid, progress))
        self._list_container.addStretch()

    def _build_goal_row(self, uid: str, progress: GoalProgress) -> QWidget:
        row = QFrame()
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setStyleSheet(f"background: {self._theme.colors.surface_alt}; border-radius: 10px;")
        layout = QVBoxLayout(row)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(4)

        header = QHBoxLayout()
        label = QLabel(_METRIC_LABELS.get(progress.goal.metric, progress.goal.metric.value))
        label.setStyleSheet(f"font-size: 11px; color: {self._theme.colors.text_primary};")
        header.addWidget(label)
        header.addStretch()

        value_label = QLabel(f"{progress.current_value}/{progress.goal.target}")
        value_label.setStyleSheet(f"font-size: 11px; color: {self._theme.colors.text_secondary};")
        header.addWidget(value_label)

        remove_button = QPushButton("✕")
        remove_button.setFixedSize(18, 18)
        remove_button.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_button.setStyleSheet(
            "background: transparent; border: none; color: #ef4444; font-size: 10px;"
        )
        remove_button.clicked.connect(lambda: self._on_remove_clicked(uid))
        header.addWidget(remove_button)
        layout.addLayout(header)

        bar = QProgressBar()
        bar.setRange(0, progress.goal.target)
        bar.setValue(progress.current_value)
        bar.setTextVisible(False)
        bar.setFixedHeight(6)
        bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                border-radius: 3px;
                background: {self._theme.colors.background};
            }}
            QProgressBar::chunk {{
                border-radius: 3px;
                background: {self._theme.colors.warning};
            }}
            """)
        layout.addWidget(bar)

        return row
