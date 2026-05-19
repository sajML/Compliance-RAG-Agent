from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.routes import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Compliance RAG Agent",
        description=(
            "Retrieval-Augmented Generation for compliance and regulatory documents. "
            "Hybrid search (vector + BM25) with source citations."
        ),
        version="1.0.0",
    )
    app.include_router(router)

    @app.exception_handler(Exception)
    async def generic_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "error_code": "INTERNAL_ERROR"},
        )

    return app


app = create_app()
