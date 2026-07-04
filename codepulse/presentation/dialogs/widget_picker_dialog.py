"""The "Add Widget" gallery: browse, preview, and add a desktop widget.

Structured as a sidebar (search + category filter + widget list) beside a
preview pane (size switcher + live preview + Add Widget button), matching
the reference design. Emits :attr:`widget_added` rather than blocking with
``exec()`` -- the caller (the desktop widget manager, Phase 5b) decides what
"adding" a widget means.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from codepulse.domain.models.widget import WidgetKind, WidgetSize
from codepulse.presentation.themes.theme import Theme
from codepulse.presentation.widgets.catalog import (
    CATEGORIES,
    SIZE_DIMENSIONS,
    WIDGET_CATALOG,
    WidgetCatalogEntry,
    get_catalog_entry,
)
from codepulse.presentation.widgets.desktop.registry import render_widget
from codepulse.presentation.windows.base_frameless_window import FramelessWindow

_DIALOG_SIZE = (760, 560)
_SIDEBAR_WIDTH = 224


class _WidgetListRow(QFrame):
    """One selectable row in the sidebar widget list."""

    clicked = Signal(object)  # emits the WidgetKind

    def __init__(
        self, entry: WidgetCatalogEntry, theme: Theme, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._entry = entry
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        icon = QLabel(entry.icon)
        icon.setFixedSize(32, 32)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        icon.setStyleSheet(
            f"background: {theme.colors.surface_alt}; border-radius: 10px; font-size: 15px;"
        )
        layout.addWidget(icon)

        text_column = QVBoxLayout()
        text_column.setSpacing(1)
        name_label = QLabel(entry.name)
        name_label.setStyleSheet(
            f"font-size: 12px; font-weight: 500; color: {theme.colors.text_primary};"
        )
        text_column.addWidget(name_label)
        category_label = QLabel(entry.category)
        category_label.setStyleSheet(f"font-size: 9px; color: {theme.colors.text_secondary};")
        text_column.addWidget(category_label)
        layout.addLayout(text_column, stretch=1)

        self.set_selected(False)

    def set_selected(self, selected: bool) -> None:
        """Toggle the highlighted/selected visual state."""
        if selected:
            self.setStyleSheet(
                "background: rgba(255, 161, 22, 0.10);"
                "border: 1px solid rgba(255, 161, 22, 0.25); border-radius: 12px;"
            )
        else:
            self.setStyleSheet(
                "background: transparent; border: 1px solid transparent; border-radius: 12px;"
            )

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._entry.kind)
        super().mousePressEvent(event)


class WidgetPickerDialog(FramelessWindow):
    """The desktop widget gallery: pick a kind and size, then add it."""

    widget_added = Signal(object, object)  # WidgetKind, WidgetSize

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(theme, always_on_top=False, resizable=False)
        if parent is not None:
            self.setParent(parent, Qt.WindowType.Dialog)

        self._category = "All"
        self._search = ""
        self._active_kind: WidgetKind | None = None
        self._active_size: WidgetSize | None = None
        self._list_rows: dict[WidgetKind, _WidgetListRow] = {}
        self._category_buttons: dict[str, QPushButton] = {}

        self.setFixedSize(*_DIALOG_SIZE)
        self._build_ui(theme)
        self._center_on_screen()

    def _center_on_screen(self) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            return
        center = screen.availableGeometry().center()
        self.move(center.x() - self.width() // 2, center.y() - self.height() // 2)

    def _build_ui(self, theme: Theme) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_sidebar(theme))
        self._preview_pane = self._build_preview_pane(theme)
        root.addWidget(self._preview_pane, stretch=1)

        self._refresh_list()
        self._show_empty_preview(theme)

    # ── Sidebar ──────────────────────────────────────────────────────────

    def _build_sidebar(self, theme: Theme) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(_SIDEBAR_WIDTH)
        sidebar.setStyleSheet(f"border-right: 1px solid {theme.colors.border};")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_sidebar_header(theme))
        layout.addWidget(self._build_category_row(theme))

        self._list_container = QVBoxLayout()
        self._list_container.setSpacing(2)
        list_widget = QWidget()
        list_widget.setLayout(self._list_container)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent; border: none;")
        scroll_area.viewport().setStyleSheet("background: transparent;")
        scroll_area.setWidget(list_widget)
        layout.addWidget(scroll_area, stretch=1)

        return sidebar

    def _build_sidebar_header(self, theme: Theme) -> QWidget:
        header = QFrame()
        header.setStyleSheet(f"border-bottom: 1px solid {theme.colors.border};")
        layout = QVBoxLayout(header)
        layout.setContentsMargins(16, 16, 16, 12)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = QLabel("Add Widget")
        title.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {theme.colors.text_primary};"
        )
        title_row.addWidget(title)
        title_row.addStretch()

        close_button = QPushButton("✕")
        close_button.setFixedSize(22, 22)
        close_button.setStyleSheet(
            f"border-radius: 11px; border: none; background: transparent;"
            f"color: {theme.colors.text_secondary}; font-size: 11px;"
        )
        close_button.clicked.connect(self.close)
        title_row.addWidget(close_button)
        layout.addLayout(title_row)

        self._search_edit = QLineEdit()
        self._search_edit.setPlaceholderText("🔍  Search widgets…")
        self._search_edit.setStyleSheet(
            f"background: {theme.colors.surface_alt}; border: 1px solid {theme.colors.border};"
            f"border-radius: 10px; padding: 6px 10px; font-size: 11px; color: {theme.colors.text_primary};"
        )
        self._search_edit.textChanged.connect(self._on_search_changed)
        layout.addWidget(self._search_edit)

        return header

    def _build_category_row(self, theme: Theme) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 4)
        layout.setSpacing(2)

        for category in CATEGORIES:
            button = QPushButton(category)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.clicked.connect(lambda _checked=False, c=category: self._on_category_selected(c))
            layout.addWidget(button)
            self._category_buttons[category] = button

        self._restyle_category_buttons(theme)
        return container

    def _restyle_category_buttons(self, theme: Theme) -> None:
        for category, button in self._category_buttons.items():
            active = category == self._category
            if active:
                button.setStyleSheet(
                    f"text-align: left; padding: 6px 12px; border-radius: 10px; border: none;"
                    f"background: rgba(255, 161, 22, 0.12); color: {theme.colors.accent};"
                    f"font-size: 12px; font-weight: 600;"
                )
            else:
                button.setStyleSheet(
                    f"text-align: left; padding: 6px 12px; border-radius: 10px; border: none;"
                    f"background: transparent; color: {theme.colors.text_secondary}; font-size: 12px;"
                )

    def _on_category_selected(self, category: str) -> None:
        self._category = category
        self._restyle_category_buttons(self.theme)
        self._refresh_list()

    def _on_search_changed(self, text: str) -> None:
        self._search = text
        self._refresh_list()

    def _filtered_entries(self) -> list[WidgetCatalogEntry]:
        needle = self._search.lower()
        return [
            entry
            for entry in WIDGET_CATALOG
            if (self._category == "All" or entry.category == self._category)
            and needle in entry.name.lower()
        ]

    def _refresh_list(self) -> None:
        while self._list_container.count():
            item = self._list_container.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()
        self._list_rows.clear()

        for entry in self._filtered_entries():
            row = _WidgetListRow(entry, self.theme)
            row.clicked.connect(self._on_widget_selected)
            row.set_selected(entry.kind == self._active_kind)
            self._list_container.addWidget(row)
            self._list_rows[entry.kind] = row
        self._list_container.addStretch()

    # ── Preview pane ─────────────────────────────────────────────────────

    def _build_preview_pane(self, theme: Theme) -> QWidget:
        pane = QWidget()
        self._preview_layout = QVBoxLayout(pane)
        self._preview_layout.setContentsMargins(0, 0, 0, 0)
        self._preview_layout.setSpacing(0)
        return pane

    def _clear_preview_pane(self) -> None:
        while self._preview_layout.count():
            item = self._preview_layout.takeAt(0)
            widget = item.widget() if item is not None else None
            if widget is not None:
                widget.deleteLater()

    def _show_empty_preview(self, theme: Theme) -> None:
        self._clear_preview_pane()
        placeholder = QWidget()
        layout = QVBoxLayout(placeholder)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        icon = QLabel("▦")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"font-size: 28px; color: {theme.colors.accent};")
        layout.addWidget(icon)

        text = QLabel("Select a widget from the list to preview it")
        text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        text.setStyleSheet(f"font-size: 12px; color: {theme.colors.text_secondary};")
        layout.addWidget(text)

        self._preview_layout.addWidget(placeholder)

    def _on_widget_selected(self, kind: WidgetKind) -> None:
        for widget_kind, row in self._list_rows.items():
            row.set_selected(widget_kind == kind)

        self._active_kind = kind
        entry = get_catalog_entry(kind)
        self._active_size = entry.sizes[0]
        self._render_active_preview()

    def _set_active_size(self, size: WidgetSize) -> None:
        self._active_size = size
        self._render_active_preview()

    def _render_active_preview(self) -> None:
        if self._active_kind is None or self._active_size is None:
            self._show_empty_preview(self.theme)
            return

        theme = self.theme
        entry = get_catalog_entry(self._active_kind)
        self._clear_preview_pane()

        self._preview_layout.addWidget(
            self._build_size_switcher(theme, entry), alignment=Qt.AlignmentFlag.AlignCenter
        )
        self._preview_layout.addStretch()
        self._preview_layout.addWidget(
            self._build_preview_card(theme), alignment=Qt.AlignmentFlag.AlignCenter
        )
        self._preview_layout.addStretch()
        self._preview_layout.addWidget(self._build_footer(theme, entry))

    def _build_size_switcher(self, theme: Theme, entry: WidgetCatalogEntry) -> QWidget:
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(6)

        for size in entry.sizes:
            button = QPushButton(size.value.capitalize())
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            active = size == self._active_size
            if active:
                button.setStyleSheet(
                    f"padding: 4px 12px; border-radius: 12px; font-size: 10px; font-weight: 700;"
                    f"background: rgba(255, 161, 22, 0.15); color: {theme.colors.accent};"
                    f"border: 1px solid rgba(255, 161, 22, 0.3);"
                )
            else:
                button.setStyleSheet(
                    f"padding: 4px 12px; border-radius: 12px; font-size: 10px; font-weight: 600;"
                    f"background: transparent; color: {theme.colors.text_secondary}; border: none;"
                )
            button.clicked.connect(lambda _checked=False, s=size: self._set_active_size(s))
            layout.addWidget(button)

        return row

    def _build_preview_card(self, theme: Theme) -> QWidget:
        assert self._active_kind is not None and self._active_size is not None
        width, height = SIZE_DIMENSIONS[self._active_size]

        card = QFrame()
        card.setFixedSize(width, height)
        card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card.setStyleSheet(
            f"background: {theme.colors.surface_alt}; border: 1px solid {theme.colors.border};"
            f"border-radius: {theme.corner_radius}px;"
        )
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        content = render_widget(self._active_kind, self._active_size, theme)
        card_layout.addWidget(content)

        return card

    def _build_footer(self, theme: Theme, entry: WidgetCatalogEntry) -> QWidget:
        footer = QFrame()
        footer.setStyleSheet(f"border-top: 1px solid {theme.colors.border};")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(20, 14, 20, 14)

        text_column = QVBoxLayout()
        text_column.setSpacing(2)
        name_label = QLabel(entry.name)
        name_label.setStyleSheet(
            f"font-size: 13px; font-weight: 600; color: {theme.colors.text_primary};"
        )
        text_column.addWidget(name_label)
        description_label = QLabel(entry.description)
        description_label.setStyleSheet(f"font-size: 10px; color: {theme.colors.text_secondary};")
        text_column.addWidget(description_label)
        layout.addLayout(text_column)
        layout.addStretch()

        add_button = QPushButton("+ Add Widget")
        add_button.setCursor(Qt.CursorShape.PointingHandCursor)
        add_button.setStyleSheet(
            f"background: {theme.colors.accent}; color: {theme.colors.background};"
            f"border-radius: 10px; padding: 8px 16px; font-size: 12px; font-weight: 700; border: none;"
        )
        add_button.clicked.connect(self._on_add_clicked)
        layout.addWidget(add_button)

        return footer

    def _on_add_clicked(self) -> None:
        if self._active_kind is None or self._active_size is None:
            return
        self.widget_added.emit(self._active_kind, self._active_size)
        self.close()
