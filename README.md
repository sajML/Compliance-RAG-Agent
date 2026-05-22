# Compliance RAG Agent

A production-style backend service that answers natural-language questions about compliance and regulatory documents using Retrieval-Augmented Generation. Upload PDFs or text files, and the system chunks, embeds, and indexes them into a vector store, then retrieves the most relevant passages at query time using **hybrid search** (vector similarity + BM25 keyword matching) merged via **Reciprocal Rank Fusion**, and generates grounded answers with **source citations**.

Built with a LangGraph agentic pipeline -- each stage is an independent node with conditional error-abort edges, making the system testable, resilient, and extensible. Dockerized and deployable to **Google Cloud Run** with CI/CD via Cloud Build.

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

### Cloud Deployment

```
┌─────────────┐     ┌──────────────────────────┐     ┌──────────────────────┐
│  Cloud Build │────►│  Artifact Registry       │────►│  Cloud Run (app)     │
│  (CI/CD)    │     │  (Docker image)          │     │  FastAPI + LangGraph │
└─────────────┘     └──────────────────────────┘     └──────────┬───────────┘
                                                                │
                    ┌──────────────────────────┐                │
                    │  Secret Manager          │────────────────┤
                    │  OPENAI_API_KEY          │                │
                    │  API_KEY, CHROMA_TOKEN   │                │
                    └──────────────────────────┘                │
                                                                │
                    ┌──────────────────────────┐                │
                    │  Cloud Run (chromadb)    │◄───────────────┘
                    │  Persistent vector store │
                    └──────────────────────────┘
```

## Features

- **Hybrid search** -- combines semantic (vector) and lexical (BM25) retrieval, merged with Reciprocal Rank Fusion for better recall than either method alone
- **Source citations** -- every answer references the exact document and page it drew from (e.g., `[1] gdpr.pdf, Page 3`)
- **Agentic pipeline** -- LangGraph StateGraph with 4 nodes and conditional error-abort at every stage
- **PDF + text ingestion** -- extracts text from PDFs via PyMuPDF, chunks with LangChain's RecursiveCharacterTextSplitter
- **Persistent vector store** -- ChromaDB with cosine similarity; local PersistentClient or remote HTTP client
- **Production-grade API** -- FastAPI with magic-byte MIME detection, file-size limits, Pydantic v2 response models, API key authentication, global exception handling
- **Cloud-native deployment** -- Dockerized, Cloud Run serverless, Cloud Build CI/CD, Secret Manager integration

## Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/ingest` | API key | Upload a PDF or text file to chunk, embed, and index |
| `POST` | `/query` | API key | Ask a question; returns answer + citations |
| `GET` | `/collection/stats` | API key | View total chunks and ingested source filenames |
| `GET` | `/health` | None | Health check for Cloud Run |
| `GET` | `/docs` | None | Interactive OpenAPI documentation (auto-generated) |

## Quick Start

### Option 1: Local (without Docker)

```bash
cd compliance-rag-agent

python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux/macOS
pip install -r requirements.txt

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

uvicorn app.main:app --reload
```

### Option 2: Docker Compose (app + ChromaDB)

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

docker compose up --build
```

This starts both the app (port 8080) and a ChromaDB server (port 8000). The app auto-connects to ChromaDB via the `CHROMA_HOST` env var.

## Usage

**1. Ingest a document:**
```bash
curl -X POST http://localhost:8080/ingest \
  -H "X-API-Key: your-key" \
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
curl -X POST http://localhost:8080/query \
  -H "X-API-Key: your-key" \
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
curl http://localhost:8080/collection/stats \
  -H "X-API-Key: your-key"
```

## Cloud Deployment (Google Cloud Run)

### Prerequisites

- GCP project with billing enabled
- `gcloud` CLI authenticated
- APIs enabled: Cloud Run, Cloud Build, Artifact Registry, Secret Manager

### 1. Create secrets in Secret Manager

```bash
echo -n "sk-your-openai-key" | gcloud secrets create openai-api-key --data-file=-
echo -n "your-app-api-key"   | gcloud secrets create app-api-key --data-file=-
echo -n "your-chroma-token"  | gcloud secrets create chroma-token --data-file=-
```

### 2. Create Artifact Registry repository

```bash
gcloud artifacts repositories create compliance-rag \
  --repository-format=docker \
  --location=europe-west1
```

### 3. Deploy ChromaDB as a Cloud Run service (one-time)

```bash
gcloud run deploy chromadb \
  --image=chromadb/chroma:latest \
  --region=europe-west1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --port=8000 \
  --memory=512Mi \
  --set-env-vars="ANONYMIZED_TELEMETRY=false,CHROMA_SERVER_AUTHN_PROVIDER=chromadb.auth.token_authn.TokenAuthenticationServerProvider" \
  --set-secrets="CHROMA_SERVER_AUTHN_CREDENTIALS=chroma-token:latest"
```

Note the service URL (e.g., `chromadb-xxxxx-ew.a.run.app`).

### 4. Deploy the app via Cloud Build

Update `_CHROMA_HOST` in `cloudbuild.yaml` with the ChromaDB service host, then:

```bash
gcloud builds submit --config=cloudbuild.yaml
```

Or set up a Cloud Build trigger for automatic deployment on git push.

### 5. Grant service-to-service auth

```bash
# Allow the app's service account to invoke the ChromaDB service
gcloud run services add-iam-policy-binding chromadb \
  --region=europe-west1 \
  --member="serviceAccount:YOUR_PROJECT_NUMBER-compute@developer.gserviceaccount.com" \
  --role="roles/run.invoker"
```

## Project Structure

```
compliance-rag-agent/
├── app/
│   ├── main.py                 # FastAPI app factory + /health endpoint
│   ├── config.py               # pydantic-settings (OpenAI, ChromaDB, auth)
│   ├── agent/
│   │   ├── state.py            # TypedDict state schema
│   │   ├── nodes.py            # Pipeline nodes: validate, retrieve, generate, format
│   │   └── graph.py            # LangGraph StateGraph with conditional edges
│   ├── api/
│   │   └── routes.py           # FastAPI endpoints + API key auth
│   ├── services/
│   │   ├── ingest.py           # Chunking, embedding, ChromaDB (local or HTTP)
│   │   ├── retriever.py        # Hybrid search (vector + BM25 + RRF)
│   │   └── text_extractor.py   # PDF text extraction via PyMuPDF
│   └── schemas/
│       └── responses.py        # Pydantic v2 response models
├── tests/                      # 25 tests (unit + integration)
├── Dockerfile                  # Python 3.12-slim, Cloud Run PORT convention
├── docker-compose.yml          # Local dev: app + ChromaDB
├── cloudbuild.yaml             # CI/CD: build, push, deploy to Cloud Run
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .dockerignore
└── .gitignore
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | -- | Required. OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o` | LLM for answer generation |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model for vector search |
| `CHROMA_HOST` | -- | ChromaDB server host (omit for local PersistentClient) |
| `CHROMA_PORT` | `8000` | ChromaDB server port |
| `CHROMA_SSL` | `false` | Use HTTPS for ChromaDB connection |
| `CHROMA_TOKEN` | -- | Bearer token for ChromaDB authentication |
| `API_KEY` | -- | API key for X-API-Key header auth (omit to disable) |
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

25 tests covering node logic, API endpoints, API key auth, health check, and retriever utilities -- all run without API keys or external services.

## Tech Stack

Python, FastAPI, LangGraph, LangChain, OpenAI API, ChromaDB, BM25 (rank-bm25), Reciprocal Rank Fusion, PyMuPDF, Pydantic v2, pydantic-settings, Uvicorn, pytest, Docker, Docker Compose, Google Cloud Run, Google Cloud Build, Google Artifact Registry, Google Secret Manager
