from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
)

logger = logging.getLogger(__name__)


class FlightDetailsView(QDialog):
    """Passive dialog showing full details for one flight."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Flight details")
        self.resize(480, 420)

        self._title = QLabel("")
        self._title.setStyleSheet("font-size: 14px; font-weight: bold;")

        self._codeshare = QLabel("")
        self._codeshare.setWordWrap(True)
        self._codeshare.setStyleSheet("color: #8a4b08; font-weight: bold;")
        self._codeshare.hide()

        self._form = QFormLayout()
        self._value_labels: dict[str, QLabel] = {}
        for key, caption in _FIELDS:
            label = QLabel("—")
            label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._value_labels[key] = label
            self._form.addRow(f"{caption}:", label)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)

        layout = QVBoxLayout(self)
        layout.addWidget(self._title)
        layout.addWidget(self._codeshare)
        layout.addLayout(self._form)
        layout.addWidget(buttons)

    def populate(self, details: dict[str, Any]) -> None:
        flight_id = details.get("flight_id") or ""
        airline = details.get("airline") or ""
        self.setWindowTitle(f"Flight details — {flight_id}")
        self._title.setText(f"{airline}  ·  {flight_id}")

        codeshare = details.get("codeshare")
        if isinstance(codeshare, dict) and (
            codeshare.get("airline_name") or codeshare.get("flight_iata")
        ):
            op_airline = codeshare.get("airline_name") or "Unknown operator"
            op_flight = codeshare.get("flight_iata") or "?"
            self._codeshare.setText(
                f"Operated by: {op_airline} ({op_flight})"
            )
            self._codeshare.show()
            logger.info("Codeshare shown for %s -> %s", flight_id, op_flight)
        else:
            self._codeshare.hide()

        mapping = {
            "status": details.get("flight_status"),
            "origin": details.get("origin"),
            "destination": details.get("destination"),
            "dep_airport": details.get("departure_airport"),
            "dep_terminal": details.get("departure_terminal"),
            "dep_gate": details.get("departure_gate"),
            "dep_time": details.get("departure_time"),
            "dep_delay": _fmt_delay(details.get("departure_delay_minutes")),
            "arr_airport": details.get("arrival_airport"),
            "arr_terminal": details.get("arrival_terminal"),
            "arr_gate": details.get("arrival_gate"),
            "arr_time": details.get("arrival_time"),
            "arr_delay": _fmt_delay(details.get("arrival_delay_minutes")),
            "aircraft": _fmt_aircraft(details),
            "price": f"${float(details.get('price') or 0):.2f}",
            "stops": details.get("stops"),
        }
        for key, value in mapping.items():
            self._value_labels[key].setText(_display(value))


_FIELDS = (
    ("status", "Status"),
    ("origin", "Origin (IATA)"),
    ("destination", "Destination (IATA)"),
    ("dep_airport", "Departure airport"),
    ("dep_terminal", "Departure terminal"),
    ("dep_gate", "Departure gate"),
    ("dep_time", "Departure time"),
    ("dep_delay", "Departure delay"),
    ("arr_airport", "Arrival airport"),
    ("arr_terminal", "Arrival terminal"),
    ("arr_gate", "Arrival gate"),
    ("arr_time", "Arrival time"),
    ("arr_delay", "Arrival delay"),
    ("aircraft", "Aircraft"),
    ("price", "Price"),
    ("stops", "Stops"),
)


def _display(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value)


def _fmt_delay(minutes: Any) -> str | None:
    if minutes is None or minutes == "":
        return None
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
