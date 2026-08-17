from __future__ import annotations

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)

_BOOKING_COLUMNS = (
    "Flight",
    "Route",
    "Passenger",
    "Passport",
    "Status",
    "Booked at",
    "Actions",
)


class BookingFormView(QDialog):
    """Small dialog to collect passenger details before booking."""

    def __init__(self, flight_id: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Book flight — {flight_id}")
        self.resize(420, 180)

        self._flight_id = flight_id
        self._passenger_name = QLineEdit()
        self._passport_number = QLineEdit()

        form = QFormLayout()
        form.addRow("Flight ID:", QLabel(flight_id))
        form.addRow("Passenger name:", self._passenger_name)
        form.addRow("Passport number:", self._passport_number)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def passenger_name(self) -> str:
        return self._passenger_name.text().strip()

    def passport_number(self) -> str:
        return self._passport_number.text().strip()


class BookingView(QWidget):
    """Passive My Bookings tab — table and signals only."""

    refresh_requested = Signal()
    cancel_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._status = QLabel("Click Refresh to load your bookings.")
        self._refresh_button = QPushButton("Refresh")
        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        self._table = QTableWidget(0, len(_BOOKING_COLUMNS))
        self._table.setHorizontalHeaderLabels(list(_BOOKING_COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(self._refresh_button)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("My Bookings"))
        layout.addLayout(button_row)
        layout.addWidget(self._status)
        layout.addWidget(self._table)

    def _on_refresh_clicked(self) -> None:
        logger.info("My Bookings refresh clicked")
        self.refresh_requested.emit()

    def set_busy(self, busy: bool) -> None:
        self._refresh_button.setEnabled(not busy)
        self._table.setEnabled(not busy)
        if busy:
            self._status.setText("Loading bookings…")

    def show_bookings(self, bookings: list[dict]) -> None:
        self._table.setRowCount(0)
        for row_index, booking in enumerate(bookings):
            self._table.insertRow(row_index)
            flight_id = str(booking.get("flight_id") or "")
            airline = booking.get("airline") or ""
            origin = booking.get("origin") or "?"
            destination = booking.get("destination") or "?"
            route = f"{origin} → {destination}"
            flight_label = f"{airline} ({flight_id})" if airline else flight_id

            self._table.setItem(row_index, 0, QTableWidgetItem(flight_label))
            self._table.setItem(row_index, 1, QTableWidgetItem(route))
            self._table.setItem(
                row_index, 2, QTableWidgetItem(str(booking.get("passenger_name") or ""))
            )
            self._table.setItem(
                row_index, 3, QTableWidgetItem(str(booking.get("passport_number") or ""))
            )
            self._table.setItem(
                row_index, 4, QTableWidgetItem(str(booking.get("status") or ""))
            )
            self._table.setItem(
                row_index, 5, QTableWidgetItem(str(booking.get("created_at") or ""))
            )

            booking_id = str(booking.get("booking_id") or "")
            status = str(booking.get("status") or "")
            if status == "active" and booking_id:
                cancel_btn = QPushButton("Cancel")
                cancel_btn.clicked.connect(
                    lambda _checked=False, bid=booking_id: self._on_cancel_clicked(bid)
                )
                self._table.setCellWidget(row_index, 6, cancel_btn)
            else:
                self._table.setItem(row_index, 6, QTableWidgetItem("—"))

        self._table.resizeColumnsToContents()
        self._status.setText(f"{len(bookings)} booking(s)")

    def _on_cancel_clicked(self, booking_id: str) -> None:
        logger.info("Cancel booking clicked booking_id=%s", booking_id)
        self.cancel_requested.emit(booking_id)

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
