from __future__ import annotations

import logging
import traceback

from PySide6.QtCore import QObject, Qt, QThread, Signal

from advisor_model import AdvisorModel
from advisor_view import AdvisorView
from session import SessionStore

logger = logging.getLogger(__name__)


class _AskWorker(QObject):
    """Runs only the HTTP call on a background thread — never touches widgets."""

    result_ready = Signal(dict)  # {"answer": str, "topics_used": list[str]}
    error_occurred = Signal(str)

    def __init__(
        self,
        model: AdvisorModel,
        question: str,
        access_token: str,
    ) -> None:
        super().__init__()
        self._model = model
        self._question = question
        self._access_token = access_token

    def run(self) -> None:
        try:
            result = self._model.ask(self._question, self._access_token)
        except Exception as exc:
            logger.error("Ask worker crashed:\n%s", traceback.format_exc())
            self.error_occurred.emit(f"Unexpected error: {exc}")
            return

        if not result.success or result.answer is None:
            self.error_occurred.emit(result.message)
            return

        self.result_ready.emit(
            {
                "answer": result.answer,
                "topics_used": list(result.topics_used or []),
            }
        )


class AdvisorPresenter(QObject):
    """Lives on the UI thread; slots update widgets safely via QueuedConnection."""

    def __init__(
        self,
        view: AdvisorView,
        model: AdvisorModel,
        session_store: SessionStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._model = model
        self._session_store = session_store
        # Strong refs — must stay alive until QThread.finished.
        self._thread: QThread | None = None
        self._worker: _AskWorker | None = None
        view.ask_requested.connect(self.on_ask)

    def on_ask(self, question: str) -> None:
        logger.info("Presenter on_ask question=%r", question[:80])
        if self._thread is not None and self._thread.isRunning():
            self._view.show_info("Ask Advisor", "Already thinking — please wait.")
            return

        session = self._session_store.session
        if session is None:
            self._view.show_error(
                "Ask Advisor",
                "You are not logged in. Please log in first (Login tab).",
            )
            return

        if len(question.strip()) < 3:
            self._view.show_error(
                "Ask Advisor",
                "Please enter a longer question (at least a few words).",
            )
            return

        # UI thread only
        self._view.set_busy(True)

        thread = QThread()
        worker = _AskWorker(self._model, question, session.access_token)
        worker.moveToThread(thread)

        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)

        # Cross-thread: worker (bg) -> presenter (UI). QueuedConnection is
        # required so these slots run on the main thread and can touch widgets.
        worker.result_ready.connect(
            self._on_result_ready,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error_occurred.connect(
            self._on_error_occurred,
            Qt.ConnectionType.QueuedConnection,
        )
        # After either outcome, quit the thread (also marshalled safely).
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)

        thread.finished.connect(
            self._on_thread_finished,
            Qt.ConnectionType.QueuedConnection,
        )

        thread.start()

    def _on_result_ready(self, payload: dict) -> None:
        """Main-thread slot — safe to update QTextEdit / clear Thinking…"""
        self._view.set_busy(False)
        answer = str(payload.get("answer") or "")
        topics = [str(t) for t in (payload.get("topics_used") or [])]
        self._view.show_answer(answer, topics)
        logger.info("Advisor answer ready topics=%s", topics)

    def _on_error_occurred(self, message: str) -> None:
        """Main-thread slot — clear Thinking… and show the error dialog."""
        self._view.set_busy(False)
        self._view.show_error("Ask Advisor", message)

    def _on_thread_finished(self) -> None:
        """Main-thread cleanup after the OS thread has fully stopped."""
        logger.info("Advisor QThread finished — clearing worker/thread refs")
        worker = self._worker
        thread = self._thread
        self._worker = None
        self._thread = None
        if worker is not None:
            worker.deleteLater()
        if thread is not None:
            thread.deleteLater()
