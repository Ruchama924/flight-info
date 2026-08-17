from __future__ import annotations

import logging
import traceback

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from theme import Colors, Spacing
from widgets.buttons import GhostButton, PrimaryButton
from widgets.inputs import FormField, StyledLineEdit

logger = logging.getLogger(__name__)

_NAV_ITEMS = (
    ("search", "Search Flights"),
    ("advisor", "Travel Advisor"),
    ("bookings", "My Bookings"),
    ("account", "Account"),
)


class LoginView(QWidget):
    """Main application shell — passive view with sidebar navigation."""

    register_requested = Signal(str, str)
    login_requested = Signal(str, str)

    def __init__(self, extra_tabs: list[tuple[str, QWidget]] | None = None) -> None:
        super().__init__()
        self.setWindowTitle("FlightAdvisor")
        self.resize(1180, 760)
        self.setMinimumSize(960, 640)

        self._user_email: str | None = None
        self._nav_buttons: dict[str, QPushButton] = {}
        self._page_index: dict[str, int] = {}

        # Auth inputs
        self._register_email = StyledLineEdit("you@example.com")
        self._register_password = StyledLineEdit("At least 6 characters")
        self._register_password.setEchoMode(StyledLineEdit.EchoMode.Password)

        self._login_email = StyledLineEdit("you@example.com")
        self._login_password = StyledLineEdit("Your password")
        self._login_password.setEchoMode(StyledLineEdit.EchoMode.Password)

        # Map extra tabs by nav key
        self._extra_pages: dict[str, QWidget] = {}
        for title, widget in extra_tabs or []:
            key = _title_to_key(title)
            self._extra_pages[key] = widget

        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), stretch=1)

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setProperty("class", "sidebar")
        sidebar.setFixedWidth(240)

        brand = QLabel("FlightAdvisor")
        brand.setStyleSheet(
            f"font-size: 20px; font-weight: 700; color: {Colors.TEXT_INVERSE}; "
            "background: transparent; padding: 4px 0;"
        )
        tagline = QLabel("Smart flight search")
        tagline.setStyleSheet(
            f"font-size: 12px; color: {Colors.SIDEBAR_TEXT}; background: transparent;"
        )

        nav_layout = QVBoxLayout()
        nav_layout.setSpacing(4)
        for key, label in _NAV_ITEMS:
            btn = QPushButton(f"  {label}")
            btn.setProperty("class", "nav")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: self._switch_page(k))
            self._nav_buttons[key] = btn
            nav_layout.addWidget(btn)

        self._user_label = QLabel("Not signed in")
        self._user_label.setWordWrap(True)
        self._user_label.setStyleSheet(
            f"color: {Colors.SIDEBAR_TEXT}; font-size: 12px; background: transparent;"
        )

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(Spacing.LG, Spacing.XL, Spacing.LG, Spacing.LG)
        layout.setSpacing(Spacing.MD)
        layout.addWidget(brand)
        layout.addWidget(tagline)
        layout.addSpacing(Spacing.LG)
        layout.addLayout(nav_layout)
        layout.addStretch()
        layout.addWidget(self._user_label)
        return sidebar

    def _build_content(self) -> QFrame:
        content = QFrame()
        content.setProperty("class", "content-area")

        self._stack = QStackedWidget()

        # Page order must match _NAV_ITEMS
        self._stack.addWidget(self._wrap_page(self._extra_pages.get("search", QWidget())))
        self._page_index["search"] = 0

        self._stack.addWidget(self._wrap_page(self._extra_pages.get("advisor", QWidget())))
        self._page_index["advisor"] = 1

        self._stack.addWidget(self._wrap_page(self._extra_pages.get("bookings", QWidget())))
        self._page_index["bookings"] = 2

        self._stack.addWidget(self._build_account_page())
        self._page_index["account"] = 3

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._stack, stretch=1)

        self._switch_page("search")
        return content

    def _wrap_page(self, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        layout = QVBoxLayout(wrapper)
        layout.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)
        layout.addWidget(widget)
        return wrapper

    def _build_account_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(Spacing.XL, Spacing.XL, Spacing.XL, Spacing.XL)

        header = QLabel("Account")
        header.setProperty("class", "page-title")
        sub = QLabel("Sign in to search flights, book tickets, and save your trips.")
        sub.setProperty("class", "page-subtitle")
        sub.setWordWrap(True)

        auth_stack = QStackedWidget()
        auth_stack.addWidget(self._build_login_card())
        auth_stack.addWidget(self._build_register_card())
        self._auth_stack = auth_stack

        toggle_row = QHBoxLayout()
        self._auth_toggle_label = QLabel("Don't have an account?")
        self._auth_toggle_label.setProperty("class", "muted")
        self._auth_toggle_btn = GhostButton("Create account")
        self._auth_toggle_btn.clicked.connect(self._toggle_auth_mode)
        toggle_row.addWidget(self._auth_toggle_label)
        toggle_row.addWidget(self._auth_toggle_btn)
        toggle_row.addStretch()

        outer.addWidget(header)
        outer.addWidget(sub)
        outer.addSpacing(Spacing.LG)
        outer.addWidget(auth_stack)
        outer.addLayout(toggle_row)
        outer.addStretch()
        return page

    def _build_login_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "auth-card")
        card.setMaximumWidth(440)

        title = QLabel("Welcome back")
        title.setProperty("class", "section-title")

        login_btn = PrimaryButton("Sign in")
        login_btn.clicked.connect(self._on_login_clicked)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(Spacing.MD)
        layout.addWidget(title)
        layout.addWidget(FormField("Email", self._login_email))
        layout.addWidget(FormField("Password", self._login_password))
        layout.addSpacing(Spacing.SM)
        layout.addWidget(login_btn)
        return card

    def _build_register_card(self) -> QFrame:
        card = QFrame()
        card.setProperty("class", "auth-card")
        card.setMaximumWidth(440)

        title = QLabel("Create your account")
        title.setProperty("class", "section-title")

        register_btn = PrimaryButton("Create account")
        register_btn.clicked.connect(self._on_register_clicked)

        layout = QVBoxLayout(card)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(Spacing.MD)
        layout.addWidget(title)
        layout.addWidget(FormField("Email", self._register_email))
        layout.addWidget(FormField("Password", self._register_password))
        layout.addSpacing(Spacing.SM)
        layout.addWidget(register_btn)
        return card

    def _toggle_auth_mode(self) -> None:
        if self._auth_stack.currentIndex() == 0:
            self._auth_stack.setCurrentIndex(1)
            self._auth_toggle_label.setText("Already have an account?")
            self._auth_toggle_btn.setText("Sign in")
        else:
            self._auth_stack.setCurrentIndex(0)
            self._auth_toggle_label.setText("Don't have an account?")
            self._auth_toggle_btn.setText("Create account")

    def _switch_page(self, key: str) -> None:
        idx = self._page_index.get(key, 0)
        self._stack.setCurrentIndex(idx)
        for nav_key, btn in self._nav_buttons.items():
            btn.setProperty("class", "nav-active" if nav_key == key else "nav")
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def set_logged_in(self, email: str | None) -> None:
        self._user_email = email
        if email:
            self._user_label.setText(f"Signed in as\n{email}")
        else:
            self._user_label.setText("Not signed in")

    def _on_register_clicked(self) -> None:
        logger.info("Register button clicked")
        try:
            self.register_requested.emit(
                self._register_email.text().strip(),
                self._register_password.text(),
            )
        except Exception:
            logger.error("ERROR in _on_register_clicked:\n%s", traceback.format_exc())

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


def _title_to_key(title: str) -> str:
    mapping = {
        "Search Flights": "search",
        "Ask Advisor": "advisor",
        "Travel Advisor": "advisor",
        "My Bookings": "bookings",
    }
    return mapping.get(title, title.lower().replace(" ", "_"))
