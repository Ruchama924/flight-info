from __future__ import annotations

import logging
import traceback

from PySide6.QtCore import QObject, Qt, QThread, Signal

from booking_model import BookingModel
from booking_view import BookingView
from session import SessionStore

logger = logging.getLogger(__name__)


class _ListBookingsWorker(QObject):
    result_ready = Signal(list)
    error_occurred = Signal(str)

    def __init__(self, model: BookingModel, access_token: str) -> None:
        super().__init__()
        self._model = model
        self._access_token = access_token

    def run(self) -> None:
        try:
            result = self._model.get_my_bookings(self._access_token)
        except Exception as exc:
            logger.error("List bookings worker crashed:\n%s", traceback.format_exc())
            self.error_occurred.emit(f"Unexpected error: {exc}")
            return

        if not result.success:
            self.error_occurred.emit(result.message)
            return

        self.result_ready.emit(list(result.bookings or []))


class _CancelBookingWorker(QObject):
    result_ready = Signal()
    error_occurred = Signal(str)

    def __init__(self, model: BookingModel, booking_id: str, access_token: str) -> None:
        super().__init__()
        self._model = model
        self._booking_id = booking_id
        self._access_token = access_token

    def run(self) -> None:
        try:
            result = self._model.cancel_booking(self._booking_id, self._access_token)
        except Exception as exc:
            logger.error("Cancel booking worker crashed:\n%s", traceback.format_exc())
            self.error_occurred.emit(f"Unexpected error: {exc}")
            return

        if not result.success:
            self.error_occurred.emit(result.message)
            return

        self.result_ready.emit()


class BookingPresenter(QObject):
    def __init__(
        self,
        view: BookingView,
        model: BookingModel,
        session_store: SessionStore,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._view = view
        self._model = model
        self._session_store = session_store
        self._thread: QThread | None = None
        self._worker: QObject | None = None

        view.refresh_requested.connect(self.on_refresh)
        view.cancel_requested.connect(self.on_cancel)

    def on_refresh(self) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._view.show_info("My Bookings", "Already loading — please wait.")
            return

        session = self._session_store.session
        if session is None:
            self._view.show_error(
                "My Bookings",
                "You are not logged in. Please log in first (Login tab).",
            )
            return

        self._view.set_busy(True)
        self._start_worker(
            _ListBookingsWorker(self._model, session.access_token),
            on_success=self._on_list_ready,
        )

    def on_cancel(self, booking_id: str) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._view.show_info("My Bookings", "Please wait for the current request.")
            return

        session = self._session_store.session
        if session is None:
            self._view.show_error(
                "My Bookings",
                "You are not logged in. Please log in first (Login tab).",
            )
            return

        self._view.set_busy(True)
        self._start_worker(
            _CancelBookingWorker(self._model, booking_id, session.access_token),
            on_success=self._on_cancel_ready,
        )

    def _start_worker(self, worker: QObject, on_success) -> None:
        thread = QThread()
        worker.moveToThread(thread)
        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)
        worker.result_ready.connect(on_success, Qt.ConnectionType.QueuedConnection)
        worker.error_occurred.connect(
            self._on_error_occurred,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(
            self._on_thread_finished,
            Qt.ConnectionType.QueuedConnection,
        )
        thread.start()

    def _on_list_ready(self, bookings: list) -> None:
        self._view.set_busy(False)
        self._view.show_bookings(bookings)

    def _on_cancel_ready(self) -> None:
        self._view.set_busy(False)
        self._view.show_info("My Bookings", "Booking cancelled.")
        self.on_refresh()

    def _on_error_occurred(self, message: str) -> None:
        self._view.set_busy(False)
        self._view.show_error("My Bookings", message)

    def _on_thread_finished(self) -> None:
        worker = self._worker
        thread = self._thread
        self._worker = None
        self._thread = None
        if worker is not None:
            worker.deleteLater()
        if thread is not None:
            thread.deleteLater()
