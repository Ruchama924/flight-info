from __future__ import annotations

import logging

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QChart,
    QChartView,
    QValueAxis,
)
from PySide6.QtCore import QDate, Qt, Signal
from PySide6.QtGui import QPainter
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
_FLIGHT_ID_ROLE = Qt.ItemDataRole.UserRole


class SearchView(QWidget):
    """Passive search form + results table + price chart (MVP View)."""

    search_requested = Signal(str, str, str)  # origin, destination, date
    details_requested = Signal(str)  # flight_id

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
        details_button = QPushButton("Details")
        details_button.clicked.connect(self._on_details_clicked)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(details_button)
        button_row.addWidget(search_button)

        self._status = QLabel("")
        self._table = QTableWidget(0, len(_COLUMNS))
        self._table.setHorizontalHeaderLabels(list(_COLUMNS))
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.cellDoubleClicked.connect(self._on_row_double_clicked)

        self._chart = QChart()
        self._chart.setTitle("Price comparison (USD)")
        self._chart.legend().setVisible(False)
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._chart_view.setMinimumHeight(220)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addLayout(button_row)
        layout.addWidget(self._status)
        layout.addWidget(self._table, stretch=2)
        layout.addWidget(QLabel("Price Comparison"))
        layout.addWidget(self._chart_view, stretch=1)

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

    def _on_details_clicked(self) -> None:
        flight_id = self._selected_flight_id()
        if not flight_id:
            self.show_error("Details", "Select a flight row first.")
            return
        logger.info("Details button clicked flight_id=%s", flight_id)
        self.details_requested.emit(flight_id)

    def _on_row_double_clicked(self, row: int, _column: int) -> None:
        item = self._table.item(row, 1)
        if item is None:
            return
        flight_id = item.data(_FLIGHT_ID_ROLE) or item.text()
        logger.info("Row double-clicked flight_id=%s", flight_id)
        self.details_requested.emit(str(flight_id))

    def _selected_flight_id(self) -> str | None:
        rows = self._table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self._table.item(rows[0].row(), 1)
        if item is None:
            return None
        return str(item.data(_FLIGHT_ID_ROLE) or item.text())

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def show_flights(self, flights: list[dict]) -> None:
        self._table.setRowCount(0)
        for flight in flights:
            row = self._table.rowCount()
            self._table.insertRow(row)
            flight_id = str(flight.get("flight_id") or "")
            values = [
                str(flight.get("airline") or ""),
                flight_id,
                str(flight.get("departure_time") or ""),
                str(flight.get("arrival_time") or ""),
                f"{float(flight.get('price') or 0):.2f}",
            ]
            for col, value in enumerate(values):
                cell = QTableWidgetItem(value)
                if col == 1:
                    cell.setData(_FLIGHT_ID_ROLE, flight_id)
                self._table.setItem(row, col, cell)

        self.update_price_chart(flights)

    def update_price_chart(self, flights: list[dict]) -> None:
        self._chart.removeAllSeries()
        for axis in list(self._chart.axes()):
            self._chart.removeAxis(axis)

        if not flights:
            self._chart.setTitle("Price comparison (USD) — no results")
            return

        # Cap labels for readability if many results (still plot all prices).
        bar_set = QBarSet("Price")
        categories: list[str] = []
        for flight in flights:
            flight_id = str(flight.get("flight_id") or "?")
            categories.append(flight_id)
            bar_set.append(float(flight.get("price") or 0))

        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)
        self._chart.setTitle(
            f"Price comparison (USD) — {len(flights)} flight(s)"
        )

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        if len(categories) > 12:
            axis_x.setLabelsAngle(-60)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("Price (USD)")
        axis_y.setLabelFormat("%.0f")
        max_price = max(float(f.get("price") or 0) for f in flights)
        axis_y.setRange(0, max(100.0, max_price * 1.15))
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        logger.info("Price chart updated with %d bars", len(categories))

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
