import filetype
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.security import APIKeyHeader

from app.agent.graph import qa_graph
from app.config import settings
from app.schemas.responses import (
    CitationResponse,
    CollectionStatsResponse,
    IngestResponse,
    QueryResponse,
)
from app.services.ingest import get_collection, ingest_pdf, ingest_text
from app.services.retriever import invalidate_bm25_cache

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(key: str = Depends(_api_key_header)):
    if not settings.api_key:
        return
    if key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    file_bytes = await file.read()

    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds {settings.max_file_size_mb} MB limit",
        )

    kind = filetype.guess(file_bytes)
    detected_mime = kind.mime if kind else None

    if detected_mime is None:
        ext = (file.filename or "").rsplit(".", 1)[-1].lower()
        if ext in ("txt", "md", "csv"):
            detected_mime = "text/plain"
        else:
            detected_mime = "application/octet-stream"

    if detected_mime == "application/pdf":
        result = ingest_pdf(file_bytes, file.filename or "document.pdf")
    elif detected_mime == "text/plain":
        text = file_bytes.decode("utf-8", errors="replace")
        result = ingest_text(text, file.filename or "document.txt")
    else:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type: {detected_mime}. Upload PDF or text files.",
        )

    invalidate_bm25_cache()

    return IngestResponse(
        filename=result["filename"],
        chunks_added=result["chunks_added"],
        message=f"Ingested {result['chunks_added']} chunks from {result['filename']}",
    )


@router.post("/query", response_model=QueryResponse)
async def query_documents(question: str = Form(...)):
    initial_state = {
        "question": question,
        "retrieved_chunks": [],
        "answer": "",
        "citations": [],
        "error": None,
    }

    result = qa_graph.invoke(initial_state)

    if result.get("error"):
        raise HTTPException(status_code=422, detail=result["error"])

    return QueryResponse(
        answer=result["answer"],
        citations=[
            CitationResponse(source=c["source"], page=c["page"], text=c["text"])
            for c in result["citations"]
        ],
        model=settings.openai_model,
        chunks_used=len(result["retrieved_chunks"]),
    )


@router.get("/collection/stats", response_model=CollectionStatsResponse)
async def collection_stats():
    collection = get_collection()
    count = collection.count()

    sources: list[str] = []
    if count > 0:
        all_meta = collection.get(include=["metadatas"])
        sources = sorted({m["source"] for m in all_meta["metadatas"]})

    return CollectionStatsResponse(total_chunks=count, sources=sources)
