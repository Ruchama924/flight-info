from __future__ import annotations

import logging
import traceback

from search_model import SearchModel
from search_view import SearchView
from session import SessionStore

logger = logging.getLogger(__name__)


class SearchPresenter:
    def __init__(
        self,
        view: SearchView,
        model: SearchModel,
        session_store: SessionStore,
    ) -> None:
        self._view = view
        self._model = model
        self._session_store = session_store
        view.search_requested.connect(self.on_search)

    def on_search(self, origin: str, destination: str, date: str) -> None:
        logger.info(
            "Presenter on_search origin=%s destination=%s date=%s",
            origin,
            destination,
            date,
        )
        try:
            session = self._session_store.session
            if session is None:
                self._view.show_error(
                    "Search",
                    "You are not logged in. Please log in first (Login tab).",
                )
                self._view.set_status("Not logged in")
                return

            if len(origin) != 3 or len(destination) != 3:
                self._view.show_error(
                    "Search",
                    "Origin and destination must be 3-letter IATA codes (e.g. JFK, LAX).",
                )
                return

            self._view.set_status("Searching…")
            result = self._model.search(
                origin=origin,
                destination=destination,
                date=date,
                access_token=session.access_token,
            )

            if not result.success:
                self._view.set_status("Search failed")
                self._view.show_error("Search", result.message)
                return

            flights = result.flights or []
            self._view.show_flights(flights)
            cache_note = "cache hit" if result.cache_hit else "cache miss (live API)"
            self._view.set_status(
                f"Found {len(flights)} flight(s) — {cache_note}"
            )
            if not flights:
                self._view.show_info(
                    "Search",
                    "No flights matched that route/date. Try busy hubs "
                    "(JFK→LAX, LHR→CDG) or today's date.",
                )
        except Exception:
            logger.error("ERROR in SearchPresenter.on_search:\n%s", traceback.format_exc())
            self._view.set_status("Unexpected error")
            self._view.show_error("Search", "Unexpected error — see terminal logs.")
