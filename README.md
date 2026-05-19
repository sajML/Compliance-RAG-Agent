# Compliance RAG Agent

A production-style backend service that answers natural-language questions about compliance and regulatory documents using Retrieval-Augmented Generation. Upload PDFs or text files, and the system chunks, embeds, and indexes them into a vector store, then retrieves the most relevant passages at query time using **hybrid search** (vector similarity + BM25 keyword matching) merged via **Reciprocal Rank Fusion**, and generates grounded answers with **source citations**.

Built with a LangGraph agentic pipeline -- each stage is an independent node with conditional error-abort edges, making the system testable, resilient, and extensible.

## Architecture

```
                          ┌──────────────────────────────────────────────┐
                          │              Ingest Pipeline                 │
  PDF / Text  ───────────►│  Extract Text ─► Chunk ─► Embed ─► ChromaDB │
                          └──────────────────────────────────────────────┘

                          ┌──────────────────────────────────────────────┐
                          │         Query Pipeline (LangGraph)           │
  Question    ───────────►│  Validate ─► Retrieve ─► Generate ─► Format │
                          │               (hybrid)    (GPT-4o)   (cite) │
                          └──────────────────────────────────────────────┘
                                          │
                                   ┌──────┴──────┐
                                   │  Hybrid     │
                                   │  Retrieval  │
                                   ├─────────────┤
                                   │ Vector      │  ChromaDB cosine
                                   │ BM25        │  rank-bm25
                                   │ Merge (RRF) │  Reciprocal Rank Fusion
                                   └─────────────┘
```

## Features

- **Hybrid search** -- combines semantic (vector) and lexical (BM25) retrieval, merged with Reciprocal Rank Fusion for better recall than either method alone
- **Source citations** -- every answer references the exact document and page it drew from (e.g., `[1] gdpr.pdf, Page 3`)
- **Agentic pipeline** -- LangGraph StateGraph with 4 nodes and conditional error-abort at every stage
- **PDF + text ingestion** -- extracts text from PDFs via PyMuPDF, chunks with LangChain's RecursiveCharacterTextSplitter
- **Persistent vector store** -- ChromaDB with cosine similarity, persisted to disk
- **Production-grade API** -- FastAPI with magic-byte MIME detection, file-size limits, Pydantic v2 response models, global exception handling

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/ingest` | Upload a PDF or text file to chunk, embed, and index |
| `POST` | `/query` | Ask a question; returns answer + citations |
| `GET` | `/collection/stats` | View total chunks and ingested source filenames |
| `GET` | `/docs` | Interactive OpenAPI documentation (auto-generated) |

## Quick Start

```bash
# Clone and enter the project
cd compliance-rag-agent

# Create virtual environment and install dependencies
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Run
uvicorn app.main:app --reload
```

## Usage

**1. Ingest a document:**
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@gdpr_regulation.pdf"
```
```json
{
  "filename": "gdpr_regulation.pdf",
  "chunks_added": 247,
  "message": "Ingested 247 chunks from gdpr_regulation.pdf"
}
```

**2. Ask a question:**
```bash
curl -X POST http://localhost:8000/query \
  -F "question=What are the data subject rights under GDPR?"
```
```json
{
  "answer": "Under GDPR, data subjects have several key rights including the right to access [1], the right to rectification [2], and the right to erasure ('right to be forgotten') [3]...",
  "citations": [
    {"source": "gdpr_regulation.pdf", "page": 12, "text": "The data subject shall have the right to obtain from the controller..."},
    {"source": "gdpr_regulation.pdf", "page": 14, "text": "The data subject shall have the right to obtain the rectification..."},
    {"source": "gdpr_regulation.pdf", "page": 15, "text": "The data subject shall have the right to obtain the erasure..."}
  ],
  "model": "gpt-4o",
  "chunks_used": 5
}
```

**3. Check collection stats:**
```bash
curl http://localhost:8000/collection/stats
```
```json
{
  "total_chunks": 247,
  "sources": ["gdpr_regulation.pdf"]
}
```

## Project Structure

```
compliance-rag-agent/
├── app/
│   ├── main.py                 # FastAPI application factory
│   ├── config.py               # pydantic-settings configuration
│   ├── agent/
│   │   ├── state.py            # TypedDict state schema (QAState, RetrievedChunk, Citation)
│   │   ├── nodes.py            # Pipeline nodes: validate, retrieve, generate, format
│   │   └── graph.py            # LangGraph StateGraph wiring with conditional edges
│   ├── api/
│   │   └── routes.py           # FastAPI endpoints (/ingest, /query, /collection/stats)
│   ├── services/
│   │   ├── ingest.py           # Chunking, embedding, ChromaDB storage
│   │   ├── retriever.py        # Hybrid search (vector + BM25 + RRF merge)
│   │   └── text_extractor.py   # PDF text extraction via PyMuPDF
│   └── schemas/
│       └── responses.py        # Pydantic v2 response models
├── tests/
│   ├── test_nodes.py           # Unit tests for pipeline nodes
│   ├── test_api.py             # Integration tests for HTTP endpoints
│   └── test_retriever.py       # Unit tests for tokenizer/retriever
├── requirements.txt
├── requirements-dev.txt
├── .env.example
└── .gitignore
```

## Configuration

All settings are configurable via environment variables or `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | -- | Required. OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | LLM for answer generation |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for vector search |
| `CHUNK_SIZE` | `512` | Characters per chunk |
| `CHUNK_OVERLAP` | `64` | Overlap between chunks |
| `RETRIEVAL_TOP_K` | `10` | Candidates retrieved per search method |
| `FINAL_TOP_K` | `5` | Chunks sent to LLM after RRF merge |
| `MAX_FILE_SIZE_MB` | `50` | Upload size limit |

## Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

21 tests covering node logic, API endpoints, and retriever utilities -- all run without API keys or external services.

## Tech Stack

Python, FastAPI, LangGraph, LangChain, OpenAI API, ChromaDB, BM25 (rank-bm25), Reciprocal Rank Fusion, PyMuPDF, Pydantic v2, pydantic-settings, Uvicorn, pytest
