from __future__ import annotations

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDateEdit, QLabel, QLineEdit, QVBoxLayout, QWidget


class StyledLineEdit(QLineEdit):
    def __init__(self, placeholder: str = "", parent=None) -> None:
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(42)


class StyledDateEdit(QDateEdit):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setDate(QDate.currentDate())
        self.setMinimumHeight(42)


class FormField(QWidget):
    """Label + input stack for consistent form spacing."""

    def __init__(self, label: str, widget: QWidget, parent=None) -> None:
        super().__init__(parent)
        lbl = QLabel(label)
        lbl.setProperty("class", "muted")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(lbl)
        layout.addWidget(widget)
