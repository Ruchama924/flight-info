import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from auth_deps import AuthenticatedUser, get_current_user
from commands.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserCommand,
    RegisterUserHandler,
)
from models.auth_schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from models.flight_schemas import FlightDetails, FlightSearchResponse
from queries.get_flight_details import (
    FlightNotFoundError,
    GetFlightDetailsHandler,
    GetFlightDetailsQuery,
)
from queries.login_user import InvalidCredentialsError, LoginQuery, LoginUserHandler
from queries.search_flights import (
    ExternalApiError,
    SearchFlightsHandler,
    SearchFlightsQuery,
)
from repositories.event_store import SQLiteEventStore

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

DB_PATH = Path(__file__).resolve().parent / "data" / "events.db"
event_store = SQLiteEventStore(DB_PATH)
register_handler = RegisterUserHandler(event_store)
login_handler = LoginUserHandler(event_store)
search_handler = SearchFlightsHandler()
details_handler = GetFlightDetailsHandler(search_handler)

app = FastAPI(title="FlightAdvisor App Server", version="0.3.0")


@app.post("/auth/register", response_model=RegisterResponse)
def register(request: RegisterRequest) -> RegisterResponse:
    try:
        event = register_handler.handle(
            RegisterUserCommand(email=str(request.email), password=request.password)
        )
    except EmailAlreadyRegisteredError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return RegisterResponse(user_id=event.user_id, email=event.email)


@app.post("/auth/login", response_model=LoginResponse)
def login(request: LoginRequest) -> LoginResponse:
    try:
        result = login_handler.handle(
            LoginQuery(email=str(request.email), password=request.password)
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return LoginResponse(
        access_token=result.access_token,
        user_id=result.user_id,
        email=result.email,
    )


@app.get("/flights/search", response_model=FlightSearchResponse)
def search_flights(
    origin: Annotated[str, Query(min_length=3, max_length=3)],
    destination: Annotated[str, Query(min_length=3, max_length=3)],
    date: Annotated[str, Query(description="Flight date YYYY-MM-DD")],
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FlightSearchResponse:
    try:
        flights, cache_hit = search_handler.handle(
            SearchFlightsQuery(origin=origin, destination=destination, date=date)
        )
    except ExternalApiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return FlightSearchResponse(
        origin=origin.strip().upper(),
        destination=destination.strip().upper(),
        date=date,
        count=len(flights),
        flights=flights,
        cache_hit=cache_hit,
    )


@app.get("/flights/{flight_id}", response_model=FlightDetails)
def get_flight_details(
    flight_id: str,
    _user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> FlightDetails:
    try:
        return details_handler.handle(GetFlightDetailsQuery(flight_id=flight_id))
    except FlightNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "app-server"}
