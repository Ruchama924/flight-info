from __future__ import annotations

import logging

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from theme import Spacing
from widgets.badges import StatusBadge
from widgets.buttons import PrimaryButton, SecondaryButton
from widgets.empty_state import EmptyState
from widgets.inputs import FormField, StyledLineEdit
from widgets.page_header import PageHeader

logger = logging.getLogger(__name__)


class BookingFormView(QDialog):
    """Booking confirmation dialog — passenger details."""

    def __init__(self, flight_id: str, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Complete your booking")
        self.resize(480, 320)

        self._flight_id = flight_id
        self._passenger_name = StyledLineEdit("Full name as on passport")
        self._passport_number = StyledLineEdit("Passport number")

        card = QFrame()
        card.setProperty("class", "auth-card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 28, 28, 28)
        card_layout.setSpacing(Spacing.MD)

        title = QLabel("Passenger details")
        title.setProperty("class", "section-title")
        flight_lbl = QLabel(f"Flight {flight_id}")
        flight_lbl.setProperty("class", "muted")

        confirm_btn = PrimaryButton("Confirm booking")
        confirm_btn.clicked.connect(self.accept)
        cancel_btn = SecondaryButton("Cancel")
        cancel_btn.clicked.connect(self.reject)

        actions = QHBoxLayout()
        actions.addStretch()
        actions.addWidget(cancel_btn)
        actions.addWidget(confirm_btn)

        card_layout.addWidget(title)
        card_layout.addWidget(flight_lbl)
        card_layout.addWidget(FormField("Passenger name", self._passenger_name))
        card_layout.addWidget(FormField("Passport number", self._passport_number))
        card_layout.addSpacing(Spacing.SM)
        card_layout.addLayout(actions)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(card)

    def passenger_name(self) -> str:
        return self._passenger_name.text().strip()

    def passport_number(self) -> str:
        return self._passport_number.text().strip()


class BookingView(QWidget):
    """Passive My Bookings screen — card list with signals only."""

    refresh_requested = Signal()
    cancel_requested = Signal(str)

    def __init__(self) -> None:
        super().__init__()

        self._status = QLabel("Sign in and click Refresh to load your bookings.")
        self._status.setProperty("class", "muted")

        self._refresh_button = SecondaryButton("Refresh")
        self._refresh_button.clicked.connect(self._on_refresh_clicked)

        toolbar = QHBoxLayout()
        toolbar.addStretch()
        toolbar.addWidget(self._refresh_button)

        self._list_container = QWidget()
        self._list_layout = QVBoxLayout(self._list_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(12)

        self._empty_state = EmptyState(
            "No bookings yet",
            "Search for a flight, open its details, and book to see your trips here.",
        )

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._list_container)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Spacing.LG)
        layout.addWidget(
            PageHeader(
                "My Bookings",
                "View and manage your flight reservations.",
            )
        )
        layout.addLayout(toolbar)
        layout.addWidget(self._status)
        layout.addWidget(scroll, stretch=1)

        self._show_empty()

    def _on_refresh_clicked(self) -> None:
        logger.info("My Bookings refresh clicked")
        self.refresh_requested.emit()

    def set_busy(self, busy: bool) -> None:
        self._refresh_button.setEnabled(not busy)
        if busy:
            self._status.setText("Loading bookings…")

    def show_bookings(self, bookings: list[dict]) -> None:
        self._clear_list()

        if not bookings:
            self._show_empty()
            self._status.setText("No bookings found")
            return

        for booking in bookings:
            self._list_layout.addWidget(self._build_booking_card(booking))

        self._list_layout.addStretch()
        self._status.setText(f"{len(bookings)} booking(s)")

    def _build_booking_card(self, booking: dict) -> QFrame:
        card = QFrame()
        card.setProperty("class", "card")

        flight_id = str(booking.get("flight_id") or "")
        airline = booking.get("airline") or ""
        origin = booking.get("origin") or "?"
        destination = booking.get("destination") or "?"
        route = f"{origin} → {destination}"
        flight_label = f"{airline} · {flight_id}" if airline else flight_id
        status = str(booking.get("status") or "")
        booking_id = str(booking.get("booking_id") or "")

        title = QLabel(flight_label)
        title.setProperty("class", "section-title")
        route_lbl = QLabel(route)
        route_lbl.setProperty("class", "muted")
        passenger = QLabel(str(booking.get("passenger_name") or ""))
        passport = QLabel(f"Passport: {booking.get('passport_number') or '—'}")
        passport.setProperty("class", "muted")
        booked = QLabel(f"Booked {booking.get('created_at') or ''}")
        booked.setProperty("class", "muted")

        badge = StatusBadge(
            "Active" if status == "active" else "Cancelled",
            status=status if status in ("active", "cancelled") else "cancelled",
        )

        left = QVBoxLayout()
        left.setSpacing(4)
        left.addWidget(title)
        left.addWidget(route_lbl)
        left.addWidget(passenger)
        left.addWidget(passport)
        left.addWidget(booked)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        right.addWidget(badge, alignment=Qt.AlignmentFlag.AlignRight)
        if status == "active" and booking_id:
            cancel_btn = QPushButton("Cancel booking")
            cancel_btn.setProperty("class", "danger")
            cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            cancel_btn.clicked.connect(
                lambda _checked=False, bid=booking_id: self._on_cancel_clicked(bid)
            )
            right.addWidget(cancel_btn, alignment=Qt.AlignmentFlag.AlignRight)

        row = QHBoxLayout(card)
        row.setContentsMargins(20, 16, 20, 16)
        row.addLayout(left, stretch=1)
        row.addLayout(right)
        return card

    def _clear_list(self) -> None:
        while self._list_layout.count():
            item = self._list_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _show_empty(self) -> None:
        self._clear_list()
        self._list_layout.addWidget(self._empty_state)

    def _on_cancel_clicked(self, booking_id: str) -> None:
        logger.info("Cancel booking clicked booking_id=%s", booking_id)
        self.cancel_requested.emit(booking_id)

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)
