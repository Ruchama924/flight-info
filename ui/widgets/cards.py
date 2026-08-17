from __future__ import annotations

from PySide6.QtWidgets import QFrame, QVBoxLayout


class CardFrame(QFrame):
    def __init__(self, hover: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("class", "card-hover" if hover else "card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        self._layout = layout

    @property
    def content_layout(self) -> QVBoxLayout:
        return self._layout
