<div align="center">

# 🛡️ Compliance RAG Agent

**Ask natural-language questions over regulatory documents and get grounded, cited answers.**

Hybrid retrieval (vector + BM25 → Reciprocal Rank Fusion) · LangGraph agentic pipeline · FastAPI · a real web UI that visualizes the pipeline as it runs · deployed on Azure Container Apps with CI/CD.

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-1C3C3C)](https://langchain-ai.github.io/langgraph/)
[![OpenAI](https://img.shields.io/badge/OpenAI-gpt--4o--mini-412991?logo=openai&logoColor=white)](https://platform.openai.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector%20store-FF6F61)](https://www.trychroma.com/)
[![Azure](https://img.shields.io/badge/Azure-Container%20Apps-0078D4?logo=microsoftazure&logoColor=white)](https://azure.microsoft.com/products/container-apps)
[![CI](https://img.shields.io/badge/CI%2FCD-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](.github/workflows/build-push.yml)
[![Tests](https://img.shields.io/badge/tests-25%20passing-success)](tests/)

### 🔗 [**Live Demo**](https://compliance-rag-agent.whitewave-2299ab7c.westeurope.azurecontainerapps.io) &nbsp;·&nbsp; login `demo123` / `demo789`

</div>

<p align="center">
  <img src="docs/demo.png" alt="Compliance RAG Agent — web UI with live pipeline visualization" width="100%">
</p>

---

## Why this project is interesting

This isn't a notebook or a thin wrapper around an LLM. It's a small but **production-shaped system**:

- **Hybrid retrieval done properly** — semantic (vector) *and* lexical (BM25) search, fused with **Reciprocal Rank Fusion** for better recall than either alone.
- **Agentic pipeline** — a **LangGraph** state machine (`validate → retrieve → generate → format`) where every stage can conditionally abort, so failures are explicit and the flow is testable.
- **Grounded & cited** — answers cite the exact **source file and page**; the model is instructed to answer *only* from retrieved context.
- **A real product, not just an API** — a polished web UI that **visualizes the pipeline and the Azure request flow as your query runs**, with login, document management, and live stats.
- **Actually deployed** — runs on **Azure Container Apps** (Chroma kept **internal-only** on the private network), built and pushed by **GitHub Actions** CI/CD, with secrets in Container Apps secrets. Also ships a **Google Cloud Run** config.
- **Tested** — 25 unit/integration tests that run with no API keys or network.

---

## 🔴 Live demo

**[compliance-rag-agent.whitewave-2299ab7c.westeurope.azurecontainerapps.io](https://compliance-rag-agent.whitewave-2299ab7c.westeurope.azurecontainerapps.io)** — login with **`demo123`** / **`demo789`**.

The **GDPR (Regulation (EU) 2016/679)** is pre-loaded, so you can ask right away:

> *"What is the right to erasure?"* · *"When must a Data Protection Officer be appointed?"* · *"What are the penalties for non-compliance?"*

Hit **Ask** and watch the pipeline light up stage by stage, then read the answer with clickable citations. You can also upload your own PDFs/text and remove documents from the knowledge base.

---

## 🏗️ How it works

```
  ┌─────────────────────────── INGEST ───────────────────────────┐
  │  PDF / Text ─► extract (PyMuPDF) ─► chunk ─► embed ─► ChromaDB │
  └───────────────────────────────────────────────────────────────┘

  ┌──────────────────── QUERY (LangGraph agent) ──────────────────┐
  │   Validate ──► Retrieve ──► Generate ──► Format                │
  │   (guardrail) (hybrid)    (gpt-4o-mini) (citations)           │
  │       └── conditional error-abort edge at every stage ──┘     │
  └───────────────────────────────────────────────────────────────┘
                              │
                  ┌───────────┴───────────┐
                  │     Hybrid Retrieval   │
                  │  Vector  → ChromaDB (cosine)
                  │  BM25    → rank-bm25 (keyword)
                  │  Fusion  → Reciprocal Rank Fusion → top-k
                  └────────────────────────┘
```

**A query, end to end:** the question is validated → embedded and run through vector search **and** BM25 in parallel → the two ranked lists are merged with RRF → the top chunks become grounding context for `gpt-4o-mini` → the answer is parsed for `[n]` markers and matched back to source/page citations.

---

## ☁️ Azure deployment architecture

```
        GitHub ──push──► GitHub Actions ──build & push──► Azure Container Registry
                                                                   │ image
                                                                   ▼
   Internet ──HTTPS──►  ┌──────────────────────────────┐   pulls from ACR
                        │  Container App:  app  (public) │
                        │  FastAPI + Web UI + LangGraph  │
                        │  secrets: OpenAI key, login,   │
                        │           session secret       │
                        └───────────────┬────────────────┘
                                        │  private env network (internal-only)
                                        ▼
                        ┌──────────────────────────────┐
                        │  Container App:  chroma        │
                        │  ChromaDB · vector store       │
                        │  NOT exposed to the internet   │
                        └──────────────────────────────┘
              both run inside one Container Apps Environment (West Europe)
```

**Design note:** Chroma uses **internal ingress** — it's reachable only by the app inside the environment, never from the public internet (an improvement over exposing it publicly with a token). The app's public ingress is login-gated.

---

## ✨ Features

| | |
|---|---|
| 🔎 **Hybrid search** | Vector + BM25 merged with Reciprocal Rank Fusion |
| 📄 **Cited answers** | Every answer references the exact document + page |
| 🧠 **Agentic pipeline** | LangGraph StateGraph, 4 nodes, conditional abort edges |
| 🎨 **Live UI** | Animated pipeline + Azure request-flow visualization |
| 🔐 **Auth** | Username/password (signed-cookie sessions) **or** `X-API-Key` for programmatic use |
| 📚 **Doc management** | Upload PDF/text and remove documents from the UI |
| 📦 **Ingestion** | PyMuPDF extraction, LangChain recursive chunking, magic-byte MIME detection, size limits |
| ⚙️ **Production API** | FastAPI, Pydantic v2 models, global exception handling, `/health` |
| ☁️ **Cloud-native** | Azure Container Apps + ACR + GitHub Actions CI/CD (and a Cloud Run config) |
| ✅ **Tested** | 25 tests, no external services required |

---

## 🎨 The "watch it think" UI

The single-page UI (vanilla JS, served by FastAPI — no build step) renders the pipeline as it runs:

- **Validate → Retrieve → Generate → Format** stages activate in sequence with a progress rail.
- The **Retrieve** stage shows vector + BM25 score bars merging via RRF, with a counter scanning the corpus.
- The **Generate** stage shows the model badge and a streaming effect; **Format** pops in citation chips.
- A separate panel animates the **Azure request flow** (Browser → Container App → ChromaDB + OpenAI).

---

## 📡 API

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/` | — | Web UI (login + ask + manage docs) |
| `POST` | `/login` · `/logout` | — | Session login / logout |
| `GET` | `/me` | — | Auth status + active model |
| `POST` | `/query` | session or API key | Ask a question → answer + citations |
| `POST` | `/ingest` | session or API key | Upload a PDF/text file to index |
| `DELETE` | `/documents?source=<name>` | session or API key | Remove a document and its chunks |
| `GET` | `/collection/stats` | session or API key | Total chunks + ingested sources |
| `GET` | `/health` | — | Health check |
| `GET` | `/docs` | — | Auto-generated OpenAPI docs |

---

## 🧰 Tech stack

**Core:** Python 3.12 · FastAPI · LangGraph · LangChain (text splitters) · OpenAI (`gpt-4o-mini` + `text-embedding-3-small`) · ChromaDB · rank-bm25 · PyMuPDF · Pydantic v2
**Web:** vanilla HTML/CSS/JS UI · Starlette `SessionMiddleware` (signed cookies)
**Infra:** Docker · Azure Container Apps · Azure Container Registry · GitHub Actions · Azure Files · (Google Cloud Run / Cloud Build config included)
**Testing:** pytest

---

## 🚀 Run locally

### Option A — Python (embedded Chroma)

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env          # add your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open http://localhost:8080. To enable the login screen locally, set `APP_USERNAME`, `APP_PASSWORD`, and `COOKIE_SECURE=false` (so the session cookie works over http).

### Option B — Docker Compose (app + ChromaDB server)

```bash
cp .env.example .env          # add your OPENAI_API_KEY
docker compose up --build
```

---

## ☁️ Deploy to Azure (Container Apps)

> CI/CD is already wired: pushing to `main` triggers **GitHub Actions** ([`.github/workflows/build-push.yml`](.github/workflows/build-push.yml)) which builds the `linux/amd64` image and pushes it to ACR. The Chroma service spec lives in [`azure/chroma.yaml`](azure/chroma.yaml).

High-level steps (full commands in the deployment notes):

```bash
# 1. resource group + registry + Container Apps environment
az group create -n rg-compliance-rag -l westeurope
az acr create -g rg-compliance-rag -n <acr> --sku Basic
az containerapp env create -n cae-compliance-rag -g rg-compliance-rag -l westeurope

# 2. deploy Chroma (internal ingress, port 8000) from azure/chroma.yaml
az containerapp create -n chroma -g rg-compliance-rag --yaml azure/chroma.yaml

# 3. deploy the app (public ingress) with secrets + the internal Chroma host
az containerapp create -n compliance-rag-agent -g rg-compliance-rag \
  --environment cae-compliance-rag \
  --image <acr>.azurecr.io/compliance-rag-agent:latest \
  --target-port 8080 --ingress external \
  --secrets openai-api-key=<key> app-password=<pw> session-secret=<rand> \
  --env-vars OPENAI_API_KEY=secretref:openai-api-key APP_USERNAME=<user> \
             APP_PASSWORD=secretref:app-password SESSION_SECRET=secretref:session-secret \
             CHROMA_HOST=chroma.internal.<env-domain> CHROMA_PORT=443 CHROMA_SSL=true
```

A **Google Cloud Run** deployment (Cloud Build + Artifact Registry + Secret Manager) is also supported via [`cloudbuild.yaml`](cloudbuild.yaml).

---

## ⚙️ Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | — | **Required.** OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | LLM for answer generation |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `APP_USERNAME` / `APP_PASSWORD` | — | Web UI login credentials |
| `SESSION_SECRET` | — | Key for signing session cookies (set in prod) |
| `COOKIE_SECURE` | `true` | `false` for local http preview |
| `API_KEY` | — | `X-API-Key` for programmatic access |
| `CHROMA_HOST` | — | Chroma server host (omit for embedded mode) |
| `CHROMA_PORT` / `CHROMA_SSL` | `8000` / `false` | Chroma connection |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `512` / `64` | Chunking |
| `RETRIEVAL_TOP_K` / `FINAL_TOP_K` | `10` / `5` | Candidates per method / chunks to LLM |
| `MAX_FILE_SIZE_MB` | `50` | Upload size limit |

---

## 🧪 Testing

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

**25 tests** covering pipeline nodes, API endpoints, auth, health, and retriever utilities — all run without API keys or external services.

---

## 📂 Project structure

```
app/
├── main.py              # FastAPI factory, session auth, login/UI routes
├── config.py            # pydantic-settings (model, Chroma, auth)
├── agent/               # LangGraph pipeline
│   ├── state.py         #   TypedDict state schema
│   ├── nodes.py         #   validate · retrieve · generate · format
│   └── graph.py         #   StateGraph + conditional edges
├── api/routes.py        # /query /ingest /documents /collection/stats (+ auth)
├── services/            # ingest · retriever (hybrid + RRF) · text_extractor
├── schemas/responses.py # Pydantic v2 models
└── web/index.html       # single-file animated UI
azure/chroma.yaml        # Chroma Container App spec (internal ingress + volume)
.github/workflows/       # GitHub Actions → ACR
cloudbuild.yaml          # Google Cloud Run CI/CD (alternative)
tests/                   # 25 tests
```

---

## 🗺️ Roadmap

- **Evaluation harness** — retrieval recall@k + answer faithfulness (RAGAS / LLM-as-judge) with a results table.
- **Durable persistence** — Azure Files NFS + VNet so the vector store survives restarts.
- **Auto-loaded default corpus** — bundle GDPR so the knowledge base is always populated.
