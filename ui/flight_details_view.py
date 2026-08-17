from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from theme import Colors, Spacing
from widgets.buttons import PrimaryButton, SecondaryButton

logger = logging.getLogger(__name__)


class FlightDetailsView(QDialog):
    """Passive dialog showing full flight details with timeline layout."""

    book_requested = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Flight details")
        self.resize(560, 640)
        self.setMinimumWidth(480)

        self._flight_id = ""
        self._price_lbl = QLabel("")
        self._price_lbl.setProperty("class", "price")

        self._header_airline = QLabel("")
        self._header_airline.setProperty("class", "section-title")

        self._header_flight = QLabel("")
        self._header_flight.setProperty("class", "muted")

        self._codeshare = QLabel("")
        self._codeshare.setWordWrap(True)
        self._codeshare.setStyleSheet(
            f"color: {Colors.WARNING}; font-weight: 600; background: {Colors.WARNING_BG}; "
            "padding: 8px 12px; border-radius: 8px;"
        )
        self._codeshare.hide()

        self._timeline_container = QWidget()
        self._timeline_layout = QVBoxLayout(self._timeline_container)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)
        self._timeline_layout.setSpacing(12)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._timeline_container)

        self._book_button = PrimaryButton("Book this flight")
        self._book_button.clicked.connect(self._on_book_clicked)
        close_btn = SecondaryButton("Close")
        close_btn.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addWidget(self._book_button)
        actions.addStretch()
        actions.addWidget(close_btn)

        card = QFrame()
        card.setProperty("class", "timeline-card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(Spacing.MD)

        header_row = QHBoxLayout()
        header_left = QVBoxLayout()
        header_left.addWidget(self._header_airline)
        header_left.addWidget(self._header_flight)
        header_row.addLayout(header_left)
        header_row.addStretch()
        header_row.addWidget(self._price_lbl)

        card_layout.addLayout(header_row)
        card_layout.addWidget(self._codeshare)
        card_layout.addWidget(scroll)
        card_layout.addLayout(actions)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(card)

    def _on_book_clicked(self) -> None:
        if self._flight_id:
            logger.info("Book this flight clicked flight_id=%s", self._flight_id)
            self.book_requested.emit(self._flight_id)

    def populate(self, details: dict[str, Any]) -> None:
        flight_id = details.get("flight_id") or ""
        self._flight_id = str(flight_id)
        airline = details.get("airline") or ""
        self.setWindowTitle(f"Flight details — {flight_id}")
        self._header_airline.setText(airline)
        self._header_flight.setText(flight_id)
        self._price_lbl.setText(f"${float(details.get('price') or 0):.2f}")

        codeshare = details.get("codeshare")
        if isinstance(codeshare, dict) and (
            codeshare.get("airline_name") or codeshare.get("flight_iata")
        ):
            op_airline = codeshare.get("airline_name") or "Unknown operator"
            op_flight = codeshare.get("flight_iata") or "?"
            self._codeshare.setText(f"Operated by {op_airline} ({op_flight})")
            self._codeshare.show()
        else:
            self._codeshare.hide()

        self._clear_timeline()
        self._add_timeline_section(
            "Departure",
            details.get("origin"),
            details.get("departure_airport"),
            details.get("departure_time"),
            terminal=details.get("departure_terminal"),
            gate=details.get("departure_gate"),
            delay=details.get("departure_delay_minutes"),
        )
        self._add_route_connector(
            details.get("origin"),
            details.get("destination"),
            details.get("stops"),
        )
        self._add_timeline_section(
            "Arrival",
            details.get("destination"),
            details.get("arrival_airport"),
            details.get("arrival_time"),
            terminal=details.get("arrival_terminal"),
            gate=details.get("arrival_gate"),
            delay=details.get("arrival_delay_minutes"),
        )
        self._add_info_row("Status", details.get("flight_status"))
        self._add_info_row("Aircraft", _fmt_aircraft(details))
        self._timeline_layout.addStretch()

    def _clear_timeline(self) -> None:
        while self._timeline_layout.count():
            item = self._timeline_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _add_timeline_section(
        self,
        title: str,
        iata: Any,
        airport: Any,
        time: Any,
        *,
        terminal: Any = None,
        gate: Any = None,
        delay: Any = None,
    ) -> None:
        frame = QFrame()
        frame.setStyleSheet(
            f"background: {Colors.SURFACE_ALT}; border-radius: 10px; border: 1px solid {Colors.BORDER};"
        )
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(4)

        title_lbl = QLabel(title)
        title_lbl.setProperty("class", "muted")
        time_lbl = QLabel(str(time or "—"))
        time_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 700; color: {Colors.TEXT}; background: transparent;"
        )
        loc = QLabel(f"{iata or '—'} · {airport or '—'}")
        loc.setProperty("class", "muted")

        layout.addWidget(title_lbl)
        layout.addWidget(time_lbl)
        layout.addWidget(loc)

        extras = []
        if terminal:
            extras.append(f"Terminal {terminal}")
        if gate:
            extras.append(f"Gate {gate}")
        if delay is not None and delay != "":
            extras.append(f"Delay {_fmt_delay(delay)}")
        if extras:
            extra_lbl = QLabel(" · ".join(extras))
            extra_lbl.setProperty("class", "muted")
            layout.addWidget(extra_lbl)

        self._timeline_layout.addWidget(frame)

    def _add_route_connector(self, origin: Any, dest: Any, stops: Any) -> None:
        stops_text = "Nonstop" if stops == 0 else f"{stops} stop(s)"
        lbl = QLabel(f"{origin or '?'} → {dest or '?'}  ·  {stops_text}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setProperty("class", "muted")
        self._timeline_layout.addWidget(lbl)

    def _add_info_row(self, label: str, value: Any) -> None:
        row = QHBoxLayout()
        key = QLabel(label)
        key.setProperty("class", "muted")
        val = QLabel(_display(value))
        val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        row.addWidget(key)
        row.addStretch()
        row.addWidget(val)
        wrapper = QWidget()
        wrapper.setLayout(row)
        self._timeline_layout.addWidget(wrapper)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def _fmt_delay(minutes: Any) -> str:
    if minutes is None or minutes == "":
        return "—"
    try:
        return f"{int(minutes)} min"
    except (TypeError, ValueError):
        return str(minutes)


def _fmt_aircraft(details: dict[str, Any]) -> str | None:
    parts = [
        details.get("aircraft_iata"),
        details.get("aircraft_icao"),
        details.get("aircraft_registration"),
    ]
    text = " / ".join(str(p) for p in parts if p)
    return text or None
