from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str = "", parent=None) -> None:
        super().__init__(parent)
        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "page-title")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(title_lbl)

        if subtitle:
            sub = QLabel(subtitle)
            sub.setProperty("class", "page-subtitle")
            sub.setWordWrap(True)
            layout.addWidget(sub)

        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
