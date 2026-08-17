from __future__ import annotations

import logging
import traceback

from PySide6.QtCore import QObject, Qt, QThread, Signal

from booking_view import BookingFormView
from booking_model import BookingModel
from flight_details_view import FlightDetailsView
from search_model import SearchModel
from session import SessionStore

logger = logging.getLogger(__name__)


class _CreateBookingWorker(QObject):
    """Runs only the HTTP call on a background thread — never touches widgets."""

    result_ready = Signal(dict)
    error_occurred = Signal(str)

    def __init__(
        self,
        model: BookingModel,
        flight_id: str,
        passenger_name: str,
        passport_number: str,
        access_token: str,
    ) -> None:
        super().__init__()
        self._model = model
        self._flight_id = flight_id
        self._passenger_name = passenger_name
        self._passport_number = passport_number
        self._access_token = access_token

    def run(self) -> None:
        try:
            result = self._model.create_booking(
                flight_id=self._flight_id,
                passenger_name=self._passenger_name,
                passport_number=self._passport_number,
                access_token=self._access_token,
            )
        except Exception as exc:
            logger.error("Create booking worker crashed:\n%s", traceback.format_exc())
            self.error_occurred.emit(f"Unexpected error: {exc}")
            return

        if not result.success or result.booking is None:
            self.error_occurred.emit(result.message)
            return

        self.result_ready.emit(result.booking)


class FlightDetailsPresenter(QObject):
    def __init__(
        self,
        model: SearchModel,
        booking_model: BookingModel,
        session_store: SessionStore,
        parent_view,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._model = model
        self._booking_model = booking_model
        self._session_store = session_store
        self._parent_view = parent_view
        self._thread: QThread | None = None
        self._worker: _CreateBookingWorker | None = None
        self._active_dialog: FlightDetailsView | None = None

    def open_details(self, flight_id: str) -> None:
        logger.info("Opening details for flight_id=%s", flight_id)
        try:
            session = self._session_store.session
            if session is None:
                self._parent_view.show_error(
                    "Details",
                    "You are not logged in. Please log in first (Login tab).",
                )
                return

            if not flight_id:
                self._parent_view.show_error("Details", "No flight selected.")
                return

            result = self._model.get_flight_details(
                flight_id=flight_id,
                access_token=session.access_token,
            )
            if not result.success or not result.details:
                self._parent_view.show_error("Details", result.message)
                return

            dialog = FlightDetailsView(self._parent_view)
            dialog.populate(result.details)
            dialog.book_requested.connect(self._on_book_requested)
            self._active_dialog = dialog
            dialog.exec()
            self._active_dialog = None
        except Exception:
            logger.error(
                "ERROR in FlightDetailsPresenter.open_details:\n%s",
                traceback.format_exc(),
            )
            self._parent_view.show_error(
                "Details", "Unexpected error — see terminal logs."
            )

    def _on_book_requested(self, flight_id: str) -> None:
        if self._thread is not None and self._thread.isRunning():
            self._parent_view.show_info("Booking", "Already submitting — please wait.")
            return

        session = self._session_store.session
        if session is None:
            self._parent_view.show_error(
                "Booking",
                "You are not logged in. Please log in first (Login tab).",
            )
            return

        form = BookingFormView(flight_id, self._active_dialog)
        if form.exec() != form.DialogCode.Accepted:
            return

        passenger_name = form.passenger_name()
        passport_number = form.passport_number()
        if not passenger_name or not passport_number:
            self._parent_view.show_error(
                "Booking",
                "Passenger name and passport number are required.",
            )
            return

        thread = QThread()
        worker = _CreateBookingWorker(
            self._booking_model,
            flight_id,
            passenger_name,
            passport_number,
            session.access_token,
        )
        worker.moveToThread(thread)
        self._thread = thread
        self._worker = worker

        thread.started.connect(worker.run)
        worker.result_ready.connect(
            self._on_booking_created,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.error_occurred.connect(
            self._on_booking_error,
            Qt.ConnectionType.QueuedConnection,
        )
        worker.result_ready.connect(thread.quit)
        worker.error_occurred.connect(thread.quit)
        thread.finished.connect(
            self._on_thread_finished,
            Qt.ConnectionType.QueuedConnection,
        )
        thread.start()

    def _on_booking_created(self, booking: dict) -> None:
        booking_id = booking.get("booking_id", "?")
        self._parent_view.show_info(
            "Booking",
            f"Flight booked successfully.\nBooking ID: {booking_id}",
        )
        if self._active_dialog is not None:
            self._active_dialog.accept()

    def _on_booking_error(self, message: str) -> None:
        self._parent_view.show_error("Booking", message)

    def _on_thread_finished(self) -> None:
        worker = self._worker
        thread = self._thread
        self._worker = None
        self._thread = None
        if worker is not None:
            worker.deleteLater()
        if thread is not None:
            thread.deleteLater()
