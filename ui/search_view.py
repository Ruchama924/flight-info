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
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from theme import Colors, Spacing
from widgets.buttons import PrimaryButton, SecondaryButton
from widgets.empty_state import EmptyState
from widgets.flight_card import FlightResultCard
from widgets.inputs import FormField, StyledDateEdit, StyledLineEdit
from widgets.page_header import PageHeader

logger = logging.getLogger(__name__)


class SearchView(QWidget):
    """Passive search form + flight cards + price chart (MVP View)."""

    search_requested = Signal(str, str, str)
    details_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._origin = StyledLineEdit("JFK")
        self._origin.setMaxLength(3)

        self._destination = StyledLineEdit("LAX")
        self._destination.setMaxLength(3)

        self._date = StyledDateEdit()

        self._status = QLabel("")
        self._status.setProperty("class", "muted")

        self._selected_flight_id: str | None = None
        self._flight_cards: list[FlightResultCard] = []

        self._results_container = QWidget()
        self._results_layout = QVBoxLayout(self._results_container)
        self._results_layout.setContentsMargins(0, 0, 0, 0)
        self._results_layout.setSpacing(10)

        self._empty_state = EmptyState(
            "Search for flights",
            "Enter origin, destination, and date above to compare available flights.",
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._results_container)
        scroll.setMinimumHeight(200)

        self._chart = QChart()
        self._chart.setBackgroundVisible(False)
        self._chart.setTitleBrush(QColor(Colors.TEXT))
        self._chart.setTitle("Price comparison")
        self._chart.legend().setVisible(False)
        self._chart_view = QChartView(self._chart)
        self._chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        self._chart_view.setMinimumHeight(240)
        self._chart_view.setStyleSheet("background: transparent;")

        chart_frame = QFrame()
        chart_frame.setProperty("class", "card")
        chart_layout = QVBoxLayout(chart_frame)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        chart_title = QLabel("Price dashboard")
        chart_title.setProperty("class", "section-title")
        chart_layout.addWidget(chart_title)
        chart_layout.addWidget(self._chart_view)

        search_btn = PrimaryButton("Search flights")
        search_btn.clicked.connect(self._on_search_clicked)
        self._details_btn = SecondaryButton("View details")
        self._details_btn.clicked.connect(self._on_details_clicked)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._details_btn)
        btn_row.addStretch()

        search_panel = QFrame()
        search_panel.setProperty("class", "search-panel")
        panel_layout = QHBoxLayout(search_panel)
        panel_layout.setContentsMargins(20, 20, 20, 20)
        panel_layout.setSpacing(Spacing.LG)

        fields = QHBoxLayout()
        fields.setSpacing(Spacing.LG)
        fields.addWidget(FormField("From", self._origin))
        fields.addWidget(FormField("To", self._destination))
        fields.addWidget(FormField("Departure", self._date))
        panel_layout.addLayout(fields, stretch=1)
        panel_layout.addWidget(search_btn)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.LG)
        layout.addWidget(
            PageHeader(
                "Find your flight",
                "Compare routes, prices, and schedules from live aviation data.",
            )
        )
        layout.addWidget(search_panel)
        layout.addLayout(btn_row)
        layout.addWidget(self._status)
        layout.addWidget(scroll, stretch=2)
        layout.addWidget(chart_frame, stretch=1)

        self._show_empty_results()

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
        if not self._selected_flight_id:
            self.show_error("Details", "Select a flight first.")
            return
        logger.info("Details button clicked flight_id=%s", self._selected_flight_id)
        self.details_requested.emit(self._selected_flight_id)

    def _on_card_selected(self, flight_id: str) -> None:
        self._selected_flight_id = flight_id
        for card in self._flight_cards:
            card.set_selected(card.flight_id() == flight_id)

    def set_status(self, text: str) -> None:
        self._status.setText(text)

    def show_flights(self, flights: list[dict]) -> None:
        self._clear_results()
        self._selected_flight_id = None

        if not flights:
            self._show_empty_results()
            self.update_price_chart(flights)
            return

        for flight in flights:
            card = FlightResultCard(flight)
            card.clicked.connect(self._on_card_selected)
            card.double_clicked.connect(self.details_requested.emit)
            self._flight_cards.append(card)
            self._results_layout.addWidget(card)

        self._results_layout.addStretch()
        self.update_price_chart(flights)

    def _clear_results(self) -> None:
        while self._results_layout.count():
            item = self._results_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
        self._flight_cards.clear()

    def _show_empty_results(self) -> None:
        self._clear_results()
        self._results_layout.addWidget(self._empty_state)

    def update_price_chart(self, flights: list[dict]) -> None:
        self._chart.removeAllSeries()
        for axis in list(self._chart.axes()):
            self._chart.removeAxis(axis)

        if not flights:
            self._chart.setTitle("Price comparison — no results yet")
            return

        bar_set = QBarSet("Price")
        bar_set.setColor(QColor(Colors.CHART_BAR))
        categories: list[str] = []
        for flight in flights:
            flight_id = str(flight.get("flight_id") or "?")
            categories.append(flight_id)
            bar_set.append(float(flight.get("price") or 0))

        series = QBarSeries()
        series.append(bar_set)
        self._chart.addSeries(series)
        self._chart.setTitle(f"Price comparison — {len(flights)} flight(s)")

        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setLabelsColor(QColor(Colors.TEXT_SECONDARY))
        if len(categories) > 10:
            axis_x.setLabelsAngle(-45)
        self._chart.addAxis(axis_x, Qt.AlignmentFlag.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = QValueAxis()
        axis_y.setTitleText("USD")
        axis_y.setLabelFormat("%.0f")
        axis_y.setLabelsColor(QColor(Colors.TEXT_SECONDARY))
        axis_y.setGridLineColor(QColor(Colors.CHART_GRID))
        max_price = max(float(f.get("price") or 0) for f in flights)
        axis_y.setRange(0, max(100.0, max_price * 1.15))
        self._chart.addAxis(axis_y, Qt.AlignmentFlag.AlignLeft)
        series.attachAxis(axis_y)

        logger.info("Price chart updated with %d bars", len(categories))

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
