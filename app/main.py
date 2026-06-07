import secrets
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import router
from app.config import settings

_WEB_DIR = Path(__file__).parent / "web"


class LoginRequest(BaseModel):
    username: str
    password: str


def _credentials_valid(username: str, password: str) -> bool:
    if not (settings.app_username and settings.app_password):
        return False
    user_ok = secrets.compare_digest(username, settings.app_username)
    pass_ok = secrets.compare_digest(password, settings.app_password)
    return user_ok and pass_ok


def create_app() -> FastAPI:
    app = FastAPI(
        title="Compliance RAG Agent",
        description=(
            "Retrieval-Augmented Generation for compliance and regulatory documents. "
            "Hybrid search (vector + BM25) with source citations."
        ),
        version="1.1.0",
    )

    # Signed-cookie sessions power the UI login. A fixed secret is required so cookies
    # stay valid across restarts and across replicas; fall back to an ephemeral one.
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret or secrets.token_hex(32),
        https_only=settings.cookie_secure,
        same_site="lax",
    )

    app.include_router(router)

    @app.get("/", include_in_schema=False)
    async def index():
        return FileResponse(str(_WEB_DIR / "index.html"))

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/me")
    async def me(request: Request):
        return {
            "authenticated": bool(request.session.get("authed")),
            "auth_required": bool(settings.app_password),
            "model": settings.openai_model,
        }

    @app.post("/login")
    async def login(payload: LoginRequest, request: Request):
        if _credentials_valid(payload.username, payload.password):
            request.session["authed"] = True
            return {"ok": True}
        raise HTTPException(status_code=401, detail="Invalid username or password")

    @app.post("/logout")
    async def logout(request: Request):
        request.session.clear()
        return {"ok": True}

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
        )

    return app


app = create_app()
