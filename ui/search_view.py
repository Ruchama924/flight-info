from __future__ import annotations

import logging

from PySide6.QtCore import QDate, Signal
from PySide6.QtWidgets import (
    QDateEdit,
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

_COLUMNS = ("Airline", "Flight", "Departure", "Arrival", "Price (USD)")


class SearchView(QWidget):
    """Passive search form + results table (MVP View)."""

    search_requested = Signal(str, str, str)  # origin, destination, date

    def __init__(self) -> None:
        super().__init__()

        self._origin = QLineEdit()
        self._origin.setPlaceholderText("e.g. JFK")
        self._origin.setMaxLength(3)

        self._destination = QLineEdit()
        self._destination.setPlaceholderText("e.g. LAX")
        self._destination.setMaxLength(3)

        self._date = QDateEdit()
        self._date.setCalendarPopup(True)
        self._date.setDisplayFormat("yyyy-MM-dd")
        self._date.setDate(QDate.currentDate())

        form = QFormLayout()
        form.addRow("Origin (IATA):", self._origin)
        form.addRow("Destination (IATA):", self._destination)
        form.addRow("Date:", self._date)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self._on_search_clicked)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(search_button)

        self._status = QLabel("")
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(list(_COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self._status)
        layout.addWidget(self._table)

    def _on_search_clicked(self) -> None:
        origin = self._origin.text().strip().upper()
        destination = self._destination.text().strip().upper()
        date = self._date.date().toString("yyyy-MM-dd")
        logger.info(
            "Search button clicked origin=%s destination=%s date=%s",
            origin,
            destination,
            date,
        )
        self.search_requested.emit(origin, destination, date)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def show_flights(self, flights: list[dict]) -> None:
        self._table.setRowCount(0)
        for flight in flights:
            row = self._table.rowCount()
            self._table.insertRow(row)
            values = [
                str(flight.get("airline") or ""),
                str(flight.get("flight_id") or ""),
                str(flight.get("departure_time") or ""),
                str(flight.get("arrival_time") or ""),
                f"{float(flight.get('price') or 0):.2f}",
            ]
            for col, value in enumerate(values):
                self._table.setItem(row, col, QTableWidgetItem(value))

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
