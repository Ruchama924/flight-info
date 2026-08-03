from __future__ import annotations

import logging
import traceback

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class LoginView(QWidget):
    """Passive view — widgets and signals only, no business logic."""

    register_requested = Signal(str, str)
    login_requested = Signal(str, str)

    def __init__(self, extra_tabs: list[tuple[str, QWidget]] | None = None) -> None:
        super().__init__()
        self.setWindowTitle("FlightAdvisor")
        self.resize(720, 480)

        self._register_email = QLineEdit()
        self._register_password = QLineEdit()
        self._register_password.setEchoMode(QLineEdit.EchoMode.Password)

        self._login_email = QLineEdit()
        self._login_password = QLineEdit()
        self._login_password.setEchoMode(QLineEdit.EchoMode.Password)

        tabs = QTabWidget()
        tabs.addTab(self._build_register_tab(), "Register")
        tabs.addTab(self._build_login_tab(), "Login")
        for title, widget in extra_tabs or []:
            tabs.addTab(widget, title)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("FlightAdvisor"))
        layout.addWidget(tabs)

    def _build_register_tab(self) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)

        form = QFormLayout()
        form.addRow("Email:", self._register_email)
        form.addRow("Password:", self._register_password)
        outer.addLayout(form)

        register_button = QPushButton("Register")
        register_button.clicked.connect(self._on_register_clicked)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(register_button)
        outer.addLayout(button_row)

        return tab

    def _build_login_tab(self) -> QWidget:
        tab = QWidget()
        outer = QVBoxLayout(tab)

        form = QFormLayout()
        form.addRow("Email:", self._login_email)
        form.addRow("Password:", self._login_password)
        outer.addLayout(form)

        login_button = QPushButton("Login")
        login_button.clicked.connect(self._on_login_clicked)

        button_row = QHBoxLayout()
        button_row.addStretch()
        button_row.addWidget(login_button)
        outer.addLayout(button_row)

        return tab

    def _on_register_clicked(self) -> None:
        logger.info("Register button clicked")
        try:
            self.register_requested.emit(
                self._register_email.text().strip(),
                self._register_password.text(),
            )
        except Exception:
            logger.error(
                "ERROR in _on_register_clicked:\n%s", traceback.format_exc()
            )

    def _on_login_clicked(self) -> None:
        logger.info("Login button clicked")
        try:
            self.login_requested.emit(
                self._login_email.text().strip(),
                self._login_password.text(),
            )
        except Exception:
            logger.error("ERROR in _on_login_clicked:\n%s", traceback.format_exc())

    def show_info(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def clear_register_form(self) -> None:
        self._register_email.clear()
        self._register_password.clear()

    def clear_login_password(self) -> None:
        self._login_password.clear()
