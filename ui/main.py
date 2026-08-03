import logging
import sys

from PySide6.QtWidgets import QApplication

from auth_model import AuthModel
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

    search_view = SearchView()
    search_model = SearchModel()
    search_presenter = SearchPresenter(search_view, search_model, session_store)

    login_view = LoginView(extra_tabs=[("Search Flights", search_view)])
    auth_model = AuthModel()
    login_presenter = LoginPresenter(login_view, auth_model, session_store)

    login_view.show()
    logger.info("UI ready — Register / Login / Search Flights")
    exit_code = app.exec()
    # Keep presenters alive for the app lifetime (avoid silent GC of slots).
    _ = (login_presenter, search_presenter)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
