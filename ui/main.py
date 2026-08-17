import logging
import sys

from PySide6.QtWidgets import QApplication

from advisor_model import AdvisorModel
from advisor_presenter import AdvisorPresenter
from advisor_view import AdvisorView
from auth_model import AuthModel
from booking_model import BookingModel
from booking_presenter import BookingPresenter
from booking_view import BookingView
from flight_details_presenter import FlightDetailsPresenter
from login_presenter import LoginPresenter
from login_view import LoginView
from search_model import SearchModel
from search_presenter import SearchPresenter
from search_view import SearchView
from session import SessionStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    app = QApplication(sys.argv)

    session_store = SessionStore()
    search_model = SearchModel()
    booking_model = BookingModel()

    search_view = SearchView()
    details_presenter = FlightDetailsPresenter(
        model=search_model,
        booking_model=booking_model,
        session_store=session_store,
        parent_view=search_view,
    )
    search_presenter = SearchPresenter(
        search_view, search_model, session_store, details_presenter
    )

    advisor_view = AdvisorView()
    advisor_model = AdvisorModel()
    advisor_presenter = AdvisorPresenter(
        advisor_view, advisor_model, session_store
    )

    booking_view = BookingView()
    booking_presenter = BookingPresenter(
        booking_view, booking_model, session_store
    )

    login_view = LoginView(
        extra_tabs=[
            ("Search Flights", search_view),
            ("Ask Advisor", advisor_view),
            ("My Bookings", booking_view),
        ]
    )
    auth_model = AuthModel()
    login_presenter = LoginPresenter(login_view, auth_model, session_store)

    login_view.show()
    logger.info("UI ready — Register / Login / Search / Ask Advisor / My Bookings")
    exit_code = app.exec()
    # Keep presenters alive for the app lifetime (avoid silent GC of slots).
    _ = (login_presenter, search_presenter, details_presenter, advisor_presenter, booking_presenter)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
