import traceback

from auth_model import AuthModel
from login_view import LoginView
from session import SessionStore


class LoginPresenter:
    def __init__(
        self,
        view: LoginView,
        model: AuthModel,
        session_store: SessionStore,
    ) -> None:
        self._view = view
        self._model = model
        self._session_store = session_store

        # Wire view signals -> presenter handlers (HTTP happens inside these).
        view.register_requested.connect(self.on_register)
        view.login_requested.connect(self.on_login)

    def on_register(self, email: str, password: str) -> None:
        print(f"Presenter on_register called with email={email!r}")
        try:
            if not email or not password:
                self._view.show_error("Register", "Email and password are required.")
                return
            if len(password) < 6:
                self._view.show_error(
                    "Register", "Password must be at least 6 characters."
                )
                return

            result = self._model.register(email, password)
            if result.success:
                self._view.show_info(
                    "Register",
                    f"Account created for {result.email}. You can log in now.",
                )
                self._view.clear_register_form()
                return

            self._view.show_error("Register", result.message)
        except Exception:
            print("ERROR in LoginPresenter.on_register:")
            traceback.print_exc()
            self._view.show_error("Register", "Unexpected error — see terminal.")

    def on_login(self, email: str, password: str) -> None:
        print(f"Presenter on_login called with email={email!r}")
        try:
            if not email or not password:
                self._view.show_error("Login", "Email and password are required.")
                return

            result = self._model.login(email, password)
            if (
                result.success
                and result.access_token
                and result.user_id
                and result.email
            ):
                self._session_store.set_session(
                    access_token=result.access_token,
                    user_id=result.user_id,
                    email=result.email,
                )
                self._view.show_info("Login", f"Logged in as {result.email}")
                self._view.clear_login_password()
                return

            self._view.show_error("Login", result.message)
        except Exception:
            print("ERROR in LoginPresenter.on_login:")
            traceback.print_exc()
            self._view.show_error("Login", "Unexpected error — see terminal.")
