import sys

from PySide6.QtWidgets import QApplication

from auth_model import AuthModel
from login_presenter import LoginPresenter
from login_view import LoginView
from session import SessionStore


def main() -> int:
    app = QApplication(sys.argv)

    view = LoginView()
    model = AuthModel()
    session_store = SessionStore()
    # Keep a strong reference — otherwise the presenter can be GC'd and
    # signal connections to on_register / on_login stop working silently.
    presenter = LoginPresenter(view, model, session_store)

    view.show()
    print("UI ready. Click Register or Login and watch this terminal.")
    exit_code = app.exec()
    # Touch presenter so it is not optimized away / collected early.
    _ = presenter
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
