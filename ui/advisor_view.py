from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class AdvisorView(QWidget):
    """Passive Ask Advisor form (MVP View)."""

    ask_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._question = QTextEdit()
        self._question.setPlaceholderText(
            "Ask a flight question, e.g. What is a layover and why is a short connection risky?"
        )
        self._question.setFixedHeight(100)

        self._ask_button = QPushButton("Ask")
        self._ask_button.clicked.connect(self._on_ask_clicked)

        self._status = QLabel("")
        self._answer = QTextEdit()
        self._answer.setReadOnly(True)
        self._answer.setPlaceholderText("Answer and referenced topics will appear here.")

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self._ask_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Your question"))
        layout.addWidget(self._question)
        layout.addLayout(button_row)
        layout.addWidget(self._status)
        layout.addWidget(QLabel("Answer"))
        layout.addWidget(self._answer)

    def _on_ask_clicked(self) -> None:
        question = self._question.toPlainText().strip()
        logger.info("Ask button clicked question=%r", question[:80])
        self.ask_requested.emit(question)

    def set_busy(self, busy: bool) -> None:
        self._ask_button.setEnabled(not busy)
        self._question.setEnabled(not busy)
        if busy:
            self._status.setText("Thinking… (local LLM may take several seconds)")
        else:
            self._status.setText("")

    def show_answer(self, answer: str, topics: list[str]) -> None:
        topics_text = ", ".join(topics) if topics else "(none)"
        self._answer.setPlainText(
            f"{answer.strip()}\n\n---\nTopics used: {topics_text}"
        )
        self._status.setText("Done")

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
        self._status.setText("Error")
