from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from theme import Colors


class FlightResultCard(QFrame):
    """Selectable flight result card for search results."""

    clicked = Signal(str)
    double_clicked = Signal(str)

    def __init__(self, flight: dict, parent=None) -> None:
        super().__init__(parent)
        self._flight_id = str(flight.get("flight_id") or "")
        self.setProperty("class", "card-hover")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFrameShape(QFrame.Shape.StyledPanel)

        airline = str(flight.get("airline") or "Unknown airline")
        dep = str(flight.get("departure_time") or "—")
        arr = str(flight.get("arrival_time") or "—")
        origin = str(flight.get("origin") or "")
        dest = str(flight.get("destination") or "")
        price = float(flight.get("price") or 0)
        stops = flight.get("stops", 0)

        left = QVBoxLayout()
        left.setSpacing(4)
        airline_lbl = QLabel(airline)
        airline_lbl.setStyleSheet(
            f"font-weight: 600; font-size: 15px; color: {Colors.TEXT}; background: transparent;"
        )
        flight_lbl = QLabel(self._flight_id)
        flight_lbl.setProperty("class", "muted")
        route_lbl = QLabel(f"{origin} → {dest}")
        route_lbl.setProperty("class", "muted")
        left.addWidget(airline_lbl)
        left.addWidget(flight_lbl)
        left.addWidget(route_lbl)

        center = QVBoxLayout()
        center.setSpacing(4)
        times = QLabel(f"{dep}  →  {arr}")
        times.setStyleSheet(f"font-weight: 500; color: {Colors.TEXT}; background: transparent;")
        stops_lbl = QLabel("Nonstop" if stops == 0 else f"{stops} stop(s)")
        stops_lbl.setProperty("class", "muted")
        center.addWidget(times)
        center.addWidget(stops_lbl)

        price_lbl = QLabel(f"${price:.0f}")
        price_lbl.setProperty("class", "price")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        row = QHBoxLayout(self)
        row.setContentsMargins(16, 14, 16, 14)
        row.setSpacing(16)
        row.addLayout(left, stretch=2)
        row.addLayout(center, stretch=3)
        row.addWidget(price_lbl, stretch=1)

    def flight_id(self) -> str:
        return self._flight_id

    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self._flight_id)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self._flight_id)
        super().mouseDoubleClickEvent(event)

    def set_selected(self, selected: bool) -> None:
        if selected:
            self.setStyleSheet(
                f"FlightResultCard, QFrame {{ background: {Colors.PRIMARY_LIGHT}; "
                f"border: 2px solid {Colors.PRIMARY}; border-radius: 12px; }}"
            )
        else:
            self.setStyleSheet("")
