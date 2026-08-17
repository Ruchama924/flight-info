from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class EmptyState(QWidget):
    def __init__(
        self,
        title: str,
        message: str,
        parent=None,
    ) -> None:
        super().__init__(parent)
        icon = QLabel("✈")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size: 36px; background: transparent;")

        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "section-title")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        msg = QLabel(message)
        msg.setProperty("class", "muted")
        msg.setWordWrap(True)
        msg.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(8)
        layout.addStretch()
        layout.addWidget(icon)
        layout.addWidget(title_lbl)
        layout.addWidget(msg)
        layout.addStretch()
