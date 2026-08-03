from pathlib import Path

from fastapi import FastAPI, HTTPException

from commands.register_user import (
    EmailAlreadyRegisteredError,
    RegisterUserCommand,
    RegisterUserHandler,
)
from models.auth_schemas import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse
from queries.login_user import InvalidCredentialsError, LoginQuery, LoginUserHandler
from repositories.event_store import SQLiteEventStore

DB_PATH = Path(__file__).resolve().parent / "data" / "events.db"
event_store = SQLiteEventStore(DB_PATH)
register_handler = RegisterUserHandler(event_store)
login_handler = LoginUserHandler(event_store)

app = FastAPI(title="FlightAdvisor App Server", version="0.1.0")


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


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "app-server"}
