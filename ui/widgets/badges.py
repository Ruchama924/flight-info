from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel


class StatusBadge(QLabel):
    def __init__(self, text: str, status: str = "active", parent=None) -> None:
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        if status == "active":
            self.setProperty("class", "badge-active")
        elif status == "cancelled":
            self.setProperty("class", "badge-cancelled")
        else:
            self.setProperty("class", "badge-warning")
        self.style().unpolish(self)
        self.style().polish(self)
