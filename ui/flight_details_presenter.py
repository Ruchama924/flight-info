from __future__ import annotations

import logging
import traceback

from flight_details_view import FlightDetailsView
from search_model import SearchModel
from session import SessionStore

logger = logging.getLogger(__name__)


class FlightDetailsPresenter:
    def __init__(
        self,
        model: SearchModel,
        session_store: SessionStore,
        parent_view,
    ) -> None:
        self._model = model
        self._session_store = session_store
        self._parent_view = parent_view

    def open_details(self, flight_id: str) -> None:
        logger.info("Opening details for flight_id=%s", flight_id)
        try:
            session = self._session_store.session
            if session is None:
                self._parent_view.show_error(
                    "Details",
                    "You are not logged in. Please log in first (Login tab).",
                )
                return

            if not flight_id:
                self._parent_view.show_error("Details", "No flight selected.")
                return

            result = self._model.get_flight_details(
                flight_id=flight_id,
                access_token=session.access_token,
            )
            if not result.success or not result.details:
                self._parent_view.show_error("Details", result.message)
                return

            dialog = FlightDetailsView(self._parent_view)
            dialog.populate(result.details)
            dialog.exec()
        except Exception:
            logger.error(
                "ERROR in FlightDetailsPresenter.open_details:\n%s",
                traceback.format_exc(),
            )
            self._parent_view.show_error(
                "Details", "Unexpected error — see terminal logs."
            )
