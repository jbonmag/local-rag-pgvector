# Local RAG with PostgreSQL and pgvector

Local-first Retrieval-Augmented Generation system for Windows 11. It uses FastAPI, PostgreSQL, pgvector, local document ingestion, hybrid retrieval, local embeddings, optional local generation and source-backed answers.

The default mode is fully mock-based, so the API, ingestion pipeline, database schema and tests can be validated without downloading large models. After models are downloaded, the project can run offline.

For a detailed step-by-step guide, read [USAGE_GUIDE.md](USAGE_GUIDE.md).

## Why this project

This repository is designed as a practical RAG reference implementation:

- local source files instead of cloud document stores;
- PostgreSQL as the system of record;
- pgvector for semantic retrieval;
- PostgreSQL full-text search for keyword retrieval;
- Reciprocal Rank Fusion to combine both result sets;
- citations and source metadata in every answer;
- deterministic mock backends for reliable tests;
- optional local Hugging Face embeddings and local LLM generation.

## Architecture

```text
Local files -> ingestion -> chunks -> embeddings -> PostgreSQL + pgvector
                                             |
Question -> hybrid retrieval -> context -> answer with sources
```

Core components:

- `data/raw`: local source documents. TXT, Markdown, HTML and PDF are supported.
- `data/processed`: local processed artifacts. Ignored by Git.
- `models`: downloaded local models. Ignored by Git.
- PostgreSQL stores documents, versions, chunks, embeddings, metadata, retrieval logs and feedback.
- `pgvector` runs vector search.
- PostgreSQL full-text search runs keyword search with `tsvector`.
- Reciprocal Rank Fusion combines vector and keyword rankings.
- FastAPI exposes `/health`, `/ingest/local` and `/query`.

## Requirements

- Windows 11
- Docker Desktop
- Python 3.11+
- PowerShell

## Quick Start: Mode A, Full Mock

This mode does not require real models.

```powershell
docker compose up -d
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts\ingest_local.py
python scripts\query.py "What do my documents say about X?"
pytest
python -m app.evals.run_evals
```

Start the API:

```powershell
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health`
- `POST /ingest/local`
- `POST /query`

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Configuration

Copy `.env.example` to `.env` and adjust values if needed.

```powershell
Copy-Item .env.example .env
```

Main settings:

```env
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/ragdb
RAG_DEFAULT_TENANT_ID=local
RAG_MIN_VECTOR_SCORE=0.75
EMBEDDINGS_BACKEND=mock
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

## PostgreSQL and Migrations

PostgreSQL runs through Docker Compose with the `pgvector/pgvector:pg16` image.

```powershell
docker compose up -d
alembic upgrade head
```

The initial migration enables `CREATE EXTENSION vector`, creates the vector column with the configured `EMBEDDING_DIMENSION`, creates an HNSW index for embeddings and creates a GIN index for full-text search.

Changing `EMBEDDING_DIMENSION` requires recreating or migrating existing embeddings and the vector column. The default value is `384`, which matches `intfloat/multilingual-e5-small`.

## Local Ingestion

Place documents in `data/raw`:

```text
data/raw/manual.md
data/raw/notes.txt
data/raw/page.html
data/raw/report.pdf
```

Run:

```powershell
python scripts\ingest_local.py
```

The ingestion pipeline:

- extracts text from supported files;
- calculates a SHA-256 hash from the extracted content;
- creates or reuses `documents`;
- creates `document_versions` only when content changes;
- performs deterministic chunking;
- generates embeddings in batches;
- avoids duplicate versions when files are unchanged.

## Querying

```powershell
python scripts\query.py "What do my documents say about X?"
```

Response contract:

```json
{
  "answer": "...",
  "sources": [
    {
      "document_id": "...",
      "chunk_id": "...",
      "title": "...",
      "source_uri": "...",
      "snippet": "..."
    }
  ],
  "retrieval_log_id": "...",
  "sufficient_context": true
}
```

If there is not enough context, `sufficient_context` is `false` and `sources` can be empty.

## Hybrid Retrieval

`app/retrieval/hybrid.py` runs:

- vector search with pgvector;
- keyword search with PostgreSQL full-text search;
- Reciprocal Rank Fusion;
- retrieval logging in `retrieval_logs`;
- a minimum vector score threshold through `RAG_MIN_VECTOR_SCORE`.

Keyword matches can still count as sufficient context. This is intentional: the project should not be reduced to vector-only retrieval unless that design change is made explicitly and tested.

## Mode B: Local Embeddings + Mock Generation

Install optional dependencies:

```powershell
pip install -e ".[local-llm]"
```

Download embeddings:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Configure:

```env
EMBEDDINGS_BACKEND=sentence_transformers
EMBEDDING_MODEL_PATH=./models/embeddings/multilingual-e5-small
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

With `ALLOW_MODEL_DOWNLOAD=false`, inference never attempts to download models at runtime. If the local folder does not exist, the error message explains what to fix.

## Mode C: Local Embeddings + Local LLM

### llama-cpp-python with GGUF

Download a specific GGUF file:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --filename MODEL_NAME.gguf --target ./models/llm/model.gguf
```

Configure:

```env
LOCAL_LLM_BACKEND=llama_cpp
LOCAL_LLM_MODEL_PATH=./models/llm/model.gguf
LOCAL_LLM_CONTEXT_SIZE=4096
LOCAL_LLM_MAX_TOKENS=512
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_N_GPU_LAYERS=0
```

On Windows, `llama-cpp-python` can require compatible wheels, CMake or build tools. GPU is not required; `LOCAL_LLM_N_GPU_LAYERS=0` runs on CPU.

### transformers with a Local Model Folder

Download a full model repository:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --target ./models/llm/MODEL_NAME
```

Configure:

```env
LOCAL_LLM_BACKEND=transformers
LOCAL_LLM_MODEL_PATH=./models/llm/MODEL_NAME
LOCAL_LLM_DEVICE=auto
LOCAL_LLM_DTYPE=auto
```

On Windows, `torch`, CUDA and `accelerate` can require environment-specific installation. The project does not require a GPU, but large models can be slow on CPU.

## Model Downloads

The download script uses `huggingface_hub` and respects `HF_TOKEN` when it is defined.

Full repository:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Single GGUF file:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --filename MODEL_NAME.gguf --target ./models/llm/model.gguf
```

`models/` is ignored by Git.

## Tests and Evals

```powershell
pytest
python -m app.evals.run_evals
```

The test suite covers hashing, chunking, RRF, mock embeddings, local backend selection, keyword query construction, context sufficiency and the answer contract.

Basic evals use `app/evals/golden.jsonl`. Positive cases require the database to be migrated and local content to be ingested.

## Data Reset

Resetting data requires an explicit flag:

```powershell
python scripts\reset_db.py --yes-i-know
```

This removes RAG table data. It does not delete files from `data/raw`.

