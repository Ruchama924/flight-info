from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from theme import Colors, Spacing
from widgets.buttons import PrimaryButton
from widgets.page_header import PageHeader

logger = logging.getLogger(__name__)


class AdvisorView(QWidget):
    """Passive AI travel advisor — chat-style interface (MVP View)."""

    ask_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._status = QLabel("")
        self._status.setProperty("class", "muted")

        self._history = QTextEdit()
        self._history.setReadOnly(True)
        self._history.setProperty("class", "chat-history")
        self._history.setPlaceholderText(
            "Your conversation will appear here. Ask about baggage, layovers, "
            "check-in times, fare classes, and more."
        )

        self._question = QTextEdit()
        self._question.setProperty("class", "chat-input")
        self._question.setPlaceholderText(
            "Ask a travel question, e.g. How early should I arrive for an international flight?"
        )
        self._question.setFixedHeight(80)

        self._ask_button = PrimaryButton("Send")
        self._ask_button.clicked.connect(self._on_ask_clicked)

        input_frame = QFrame()
        input_frame.setProperty("class", "card")
        input_layout = QVBoxLayout(input_frame)
        input_layout.setContentsMargins(16, 16, 16, 16)
        input_layout.setSpacing(Spacing.SM)
        input_layout.addWidget(self._question)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(self._ask_button)
        input_layout.addLayout(btn_row)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.LG)
        layout.addWidget(
            PageHeader(
                "Travel Advisor",
                "Get instant answers powered by local AI and curated travel knowledge.",
            )
        )
        layout.addWidget(self._status)
        layout.addWidget(self._history, stretch=1)
        layout.addWidget(input_frame)

        self._append_system_message(
            "Hello! I'm your FlightAdvisor assistant. Ask me anything about flying."
        )

    def _on_ask_clicked(self) -> None:
        question = self._question.toPlainText().strip()
        logger.info("Ask button clicked question=%r", question[:80])
        if question:
            self._append_user_message(question)
            self._question.clear()
        self.ask_requested.emit(question)

    def set_busy(self, busy: bool) -> None:
        self._ask_button.setEnabled(not busy)
        self._question.setEnabled(not busy)
        if busy:
            self._status.setText("Thinking… this may take a few seconds")
            self._append_typing_indicator()
        else:
            self._status.setText("")

    def show_answer(self, answer: str, topics: list[str]) -> None:
        self._remove_typing_indicator()
        topics_text = ", ".join(topics) if topics else "general travel"
        self._append_assistant_message(answer.strip(), topics_text)
        self._status.setText("Ready")

    def _append_user_message(self, text: str) -> None:
        self._append_html_block(text, "You", Colors.PRIMARY_LIGHT, Colors.TEXT)

    def _append_assistant_message(self, text: str, topics: str) -> None:
        body = f"{text}<br><br><span style='color:{Colors.TEXT_MUTED}; font-size:11px;'>"
        body += f"Topics: {topics}</span>"
        self._append_html_block(body, "Advisor", Colors.SURFACE_ALT, Colors.TEXT, raw=True)

    def _append_system_message(self, text: str) -> None:
        self._append_html_block(text, "FlightAdvisor", Colors.SURFACE_ALT, Colors.TEXT_SECONDARY)

    def _append_typing_indicator(self) -> None:
        self._history.append(
            f"<p style='color:{Colors.TEXT_MUTED}; margin:8px 0;'><i>Advisor is typing…</i></p>"
        )

    def _remove_typing_indicator(self) -> None:
        html = self._history.toHtml()
        marker = "<i>Advisor is typing…</i>"
        if marker in html:
            idx = html.rfind(marker)
            if idx > 0:
                start = html.rfind("<p", 0, idx)
                self._history.setHtml(html[:start] if start > 0 else html.replace(marker, ""))

    def _append_html_block(
        self,
        text: str,
        sender: str,
        bg: str,
        color: str,
        *,
        raw: bool = False,
    ) -> None:
        body = text if raw else _escape_html(text)
        html = (
            f"<div style='margin: 10px 0; padding: 12px 14px; background:{bg}; "
            f"border-radius: 10px; color:{color};'>"
            f"<div style='font-weight:600; font-size:12px; margin-bottom:6px;'>{sender}</div>"
            f"<div style='line-height:1.5;'>{body}</div></div>"
        )
        self._history.append(html)

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
        self._status.setText("Error")
        self._remove_typing_indicator()


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("\n", "<br>")
    )
