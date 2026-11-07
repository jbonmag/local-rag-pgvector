# Local RAG Usage Guide

This guide explains how to run, understand and maintain this local RAG project.

The project is intentionally practical: put documents in a local folder, ingest them, ask a question, retrieve relevant chunks, generate an answer and return the sources used to build that answer.

## 1. What This Project Does

RAG means Retrieval-Augmented Generation.

In plain terms:

- retrieval means searching for relevant information;
- augmented means using that retrieved information as context;
- generation means producing the final answer.

This is not a chatbot that answers only from model memory. It first searches your local documents and then answers from the retrieved context.

## 2. Mental Model

Think of the system as a small local library:

1. You place documents in `data/raw`.
2. The ingestion pipeline reads them.
3. The text is split into small chunks.
4. Chunks are stored in PostgreSQL.
5. Embeddings are generated for semantic search.
6. Keyword indexes are generated for text search.
7. A question runs both searches.
8. Results are fused and ranked.
9. The answer is generated with citations.

The main rule is simple:

```text
No reliable sources, no reliable answer.
```

## 3. What It Does Not Require

The project is designed to run locally after dependencies and models are downloaded.

It does not require:

- cloud document storage;
- hosted inference APIs as the main backend;
- LM Studio;
- Ollama;
- external inference servers.

The default `mock` mode makes the whole application testable without heavy models.

## 4. Main Components

```text
FastAPI
PostgreSQL
pgvector
Local ingestion
Local embeddings
Hybrid retrieval
Mock or local generation
Evaluations
Tests
```

### FastAPI

FastAPI exposes the HTTP API.

Included endpoints:

- `GET /health`: checks that the API is running.
- `POST /ingest/local`: ingests documents from `data/raw`.
- `POST /query`: asks a question.

### PostgreSQL

PostgreSQL stores:

- documents;
- document versions;
- chunks;
- embeddings;
- retrieval logs;
- feedback.

Original source files remain on disk in `data/raw`.

### pgvector

pgvector is a PostgreSQL extension that stores vectors and runs vector similarity search.

An embedding is a vector representation of text:

```text
[0.12, -0.03, 0.44, ...]
```

In this project, embeddings represent chunk meaning.

### Local Ingestion

The ingestion process reads files from `data/raw`.

Supported file types:

- `.txt`
- `.md`
- `.markdown`
- `.html`
- `.htm`
- `.pdf`

The pipeline:

1. Finds supported files.
2. Extracts text.
3. Calculates a SHA-256 content hash.
4. Creates or reuses the document record.
5. Creates a new document version only when content changes.
6. Splits text into chunks.
7. Generates embeddings.
8. Stores everything in PostgreSQL.

### Embeddings

An embedding converts text into numbers so the system can search by meaning.

Example:

```text
Question: "internal rules"
Document: "company policies"
```

Even if the words differ, semantic retrieval can still find related chunks.

Supported embedding backends:

- `mock`
- `sentence_transformers`

The `mock` backend is deterministic and useful for development and tests. The `sentence_transformers` backend uses local Hugging Face models.

### Hybrid Retrieval

This project does not use vector search alone.

Hybrid retrieval means:

```text
vector search + keyword search
```

Vector search finds meaning-based matches. Keyword search finds exact or close textual matches. Reciprocal Rank Fusion combines both lists.

### Generation

The generation layer writes the final answer.

Supported backends:

- `mock`
- `llama_cpp`
- `transformers`

The `mock` backend always works and does not require a real model. The other backends load local models from disk.

## 5. Project Structure

```text
.
|-- AGENTS.md
|-- README.md
|-- USAGE_GUIDE.md
|-- .env.example
|-- docker-compose.yml
|-- pyproject.toml
|-- alembic.ini
|-- app/
|-- migrations/
|-- scripts/
|-- tests/
|-- data/
|   |-- raw/
|   `-- processed/
`-- models/
    |-- llm/
    `-- embeddings/
```

Important folders:

- `data/raw`: original local documents.
- `data/processed`: optional processed artifacts, ignored by Git.
- `models`: downloaded local models, ignored by Git.
- `app/api`: FastAPI endpoints.
- `app/ingestion`: loaders, hashing and chunking.
- `app/retrieval`: hybrid retrieval.
- `app/llm`: embeddings and local generation.
- `app/evals`: basic evaluation runner and golden examples.
- `migrations`: Alembic migrations.
- `scripts`: command-line utilities.
- `tests`: unit and integration-style tests.

## 6. Requirements

You need:

- Windows 11;
- Docker Desktop;
- Python 3.11 or newer;
- PowerShell;
- internet access only for dependency installation and model downloads.

After downloading models, the system can run offline.

## 7. First Run

Open PowerShell in the project folder.

### 7.1 Start PostgreSQL

```powershell
docker compose up -d
```

This starts PostgreSQL with pgvector.

### 7.2 Create and Activate a Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### 7.3 Install Dependencies

For the default mode and tests:

```powershell
pip install -e ".[dev]"
```

This installs the API, database, ingestion and test dependencies. It does not install heavy local model dependencies.

### 7.4 Create Database Tables

```powershell
alembic upgrade head
```

This creates the PostgreSQL schema and enables the `vector` extension.

### 7.5 Add Documents

Put source documents in:

```text
data/raw
```

Example:

```text
data/raw/notes.md
```

### 7.6 Ingest Documents

```powershell
python scripts\ingest_local.py
```

Expected shape:

```json
{
  "tenant_id": "local",
  "files_seen": 1,
  "documents_created": 1,
  "versions_created": 1,
  "chunks_created": 1,
  "embeddings_created": 1,
  "skipped_unchanged": 0,
  "errors": []
}
```

If you run ingestion again without changing files, it should be idempotent:

```json
{
  "documents_created": 0,
  "versions_created": 0,
  "chunks_created": 0,
  "embeddings_created": 0,
  "skipped_unchanged": 1
}
```

### 7.7 Ask a Question

```powershell
python scripts\query.py "What do my documents say about internal policies?"
```

Expected response shape:

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

Key fields:

- `answer`: generated answer.
- `sources`: evidence used to answer.
- `retrieval_log_id`: retrieval trace identifier.
- `sufficient_context`: whether the system found enough context.

## 8. Running the API

Start FastAPI:

```powershell
uvicorn app.main:app --reload
```

Default URL:

```text
http://127.0.0.1:8000
```

Interactive documentation:

```text
http://127.0.0.1:8000/docs
```

### Health Check

```text
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Ingest from the API

```text
POST /ingest/local
```

Optional body:

```json
{
  "tenant_id": "local"
}
```

### Query from the API

```text
POST /query
```

Body:

```json
{
  "question": "What do my documents say about internal policies?",
  "tenant_id": "local",
  "top_k": 5
}
```

## 9. What Happens During Ingestion

When you add a file such as:

```text
data/raw/notes.md
```

the system performs these steps:

1. Finds supported files in `data/raw`.
2. Extracts plain text.
3. Calculates a SHA-256 hash.
4. Creates or reuses a `documents` row.
5. Creates or reuses a `document_versions` row.
6. Splits text into chunks with overlap.
7. Generates an embedding for each chunk.
8. Stores chunks and embeddings in PostgreSQL.

The content hash is used for versioning. If the text changes, the hash changes and a new version is created. If the text is unchanged, the system avoids duplicate data.

## 10. Database Tables

### `documents`

Represents a source document.

Important fields:

- `id`
- `tenant_id`
- `source_type`
- `source_uri`
- `title`
- `metadata`
- `created_at`

### `document_versions`

Represents a specific version of a document.

Important fields:

- `id`
- `document_id`
- `content_hash`
- `version_label`
- `created_at`

Important rule:

```text
unique(document_id, content_hash)
```

This prevents duplicate versions.

### `chunks`

Stores text chunks.

Important fields:

- `id`
- `document_version_id`
- `tenant_id`
- `chunk_index`
- `content`
- `metadata`
- `token_count`
- `search_vector`

`search_vector` is generated by PostgreSQL for full-text search.

### `chunk_embeddings`

Stores vector embeddings.

Important fields:

- `chunk_id`
- `embedding`
- `embedding_model`
- `embedding_dimension`
- `created_at`

The default dimension is `384`.

### `retrieval_logs`

Stores retrieval traces for later inspection.

Important fields:

- `query`
- `tenant_id`
- `retrieved_chunk_ids`
- `scores`

### `feedback`

Stores human feedback.

Important fields:

- `retrieval_log_id`
- `rating`
- `comment`

## 11. How Hybrid Retrieval Works

Each question runs two retrieval paths.

### Vector Search

1. The question is converted into an embedding.
2. The question embedding is compared with chunk embeddings.
3. Similar chunks are retrieved by meaning.

This can find related text even when wording differs.

### Keyword Search

1. The question is normalized.
2. Common words are filtered.
3. Important terms are searched through PostgreSQL full-text search.

This catches exact terms, names, identifiers and domain-specific keywords.

### Reciprocal Rank Fusion

The system gets:

```text
vector results
keyword results
```

RRF combines both rankings. A chunk that ranks well in both lists usually receives a stronger final rank.

## 12. Context Sufficiency

The system should not invent answers.

Context is considered sufficient when:

- there is a keyword match; or
- there is a vector match above `RAG_MIN_VECTOR_SCORE`.

If there is not enough context, the system returns:

```text
There is not enough information in the local documents to answer.
```

and:

```json
{
  "sources": [],
  "sufficient_context": false
}
```

## 13. Usage Modes

### Mode A: Full Mock

Default mode.

```env
EMBEDDINGS_BACKEND=mock
LOCAL_LLM_BACKEND=mock
```

Use it to validate:

- Docker setup;
- migrations;
- ingestion;
- endpoints;
- tests;
- the complete RAG flow.

This mode is not intended to measure real model quality.

### Mode B: Local Embeddings + Mock Generation

Configuration:

```env
EMBEDDINGS_BACKEND=sentence_transformers
EMBEDDING_MODEL_PATH=./models/embeddings/multilingual-e5-small
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

Download the embedding model:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Use this mode to test real semantic retrieval without loading a large LLM.

### Mode C: Local Embeddings + Local LLM

This mode uses real embeddings and real local generation.

Supported generation backends:

- `llama_cpp`
- `transformers`

#### llama-cpp-python with GGUF

Configuration:

```env
LOCAL_LLM_BACKEND=llama_cpp
LOCAL_LLM_MODEL_PATH=./models/llm/model.gguf
LOCAL_LLM_CONTEXT_SIZE=4096
LOCAL_LLM_MAX_TOKENS=512
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_N_GPU_LAYERS=0
```

Download a GGUF file:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --filename MODEL_NAME.gguf --target ./models/llm/model.gguf
```

Install optional dependencies:

```powershell
pip install -e ".[local-llm]"
```

#### transformers with a Local Folder

Configuration:

```env
LOCAL_LLM_BACKEND=transformers
LOCAL_LLM_MODEL_PATH=./models/llm/MODEL_NAME
LOCAL_LLM_DEVICE=auto
LOCAL_LLM_DTYPE=auto
```

Download a local model folder:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --target ./models/llm/MODEL_NAME
```

## 14. Environment Variables

Base file:

```text
.env.example
```

Copy it:

```powershell
Copy-Item .env.example .env
```

### Database

```env
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/ragdb
```

Meaning:

- user: `rag`
- password: `rag`
- host: `localhost`
- port: `5432`
- database: `ragdb`

### Default Tenant

```env
RAG_DEFAULT_TENANT_ID=local
```

A tenant is a namespace. The project currently uses `local`, but the schema is designed to avoid mixing scopes.

### Vector Threshold

```env
RAG_MIN_VECTOR_SCORE=0.80
```

This helps prevent weak semantic matches from being treated as enough context.

The right value depends on the embedding model. E5 models give high cosine similarities even to unrelated text. With `intfloat/multilingual-e5-small` and the example document:

- questions about the document scored 0.86-0.87;
- unrelated questions scored 0.72-0.76: a password, the weather on Mars, a paella recipe.

The old default of 0.75 let some of the unrelated ones through; 0.80 separates them. This was calibrated on a handful of questions, so check it against your own documents and questions, and recalibrate if you change the model.

### Embeddings

```env
EMBEDDINGS_BACKEND=mock
EMBEDDING_MODEL_PATH=./models/embeddings/model
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
```

If `EMBEDDING_DIMENSION` changes, existing embeddings and the vector column must be recreated or migrated.

### Downloads

```env
ALLOW_MODEL_DOWNLOAD=false
HF_TOKEN=
```

With `ALLOW_MODEL_DOWNLOAD=false`, runtime inference does not download models automatically.

## 15. Downloading Models

Download a full repository:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Download a single GGUF file:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --filename MODEL_NAME.gguf --target ./models/llm/model.gguf
```

If a model requires authentication, define:

```env
HF_TOKEN=your_token
```

Never commit `.env`.

## 16. Tests

Run:

```powershell
pytest
```

The test suite checks:

- deterministic hashing;
- chunking;
- RRF;
- mock embeddings;
- clear errors when local models are missing;
- answer contract;
- context sufficiency;
- keyword query construction.

## 17. Evals

Run:

```powershell
python -m app.evals.run_evals
```

The evals use:

```text
app/evals/golden.jsonl
```

They include positive and negative examples:

- positive cases should answer with sources;
- negative cases should refuse when context is insufficient.

Expected shape:

```json
{"total": 3, "passed": 3, "pass_rate": 1.0}
```

## 18. Resetting Data

The reset script is intentionally guarded:

```powershell
python scripts\reset_db.py --yes-i-know
```

It deletes RAG table data. It does not delete files in `data/raw`.

## 19. Common Issues

### Docker Does Not Start

Make sure Docker Desktop is running.

```powershell
docker compose up -d
```

### Alembic Cannot Connect

Check that PostgreSQL is running:

```powershell
docker ps
```

### Ingestion Finds No Documents

Check that files are inside:

```text
data/raw
```

and that extensions are supported:

```text
.txt
.md
.markdown
.html
.htm
.pdf
```

### The Answer Has No Sources

If `sufficient_context=false`, empty `sources` is expected. It means the system did not find enough evidence.

### Embedding Model Changes Break the Database

If you change the vector dimension, for example from `384` to `768`, you must recreate or migrate embeddings and the vector column.

### No GPU Available

Mock mode does not require a GPU.

Real local models can run on CPU, but large models may be slow.

### `llama-cpp-python` Installation Fails

On Windows, it can require compatible wheels, CMake or build tools.

The project can still run with:

```env
LOCAL_LLM_BACKEND=mock
```

## 20. Good Practices

### Do Not Commit Models

`models/` is ignored by Git. Model files can be several GB.

### Do Not Commit Secrets

Do not commit:

- `.env`;
- tokens;
- passwords;
- private documents;
- sensitive logs.

### Be Careful with `data/raw`

Real source documents are ignored by default.

The rule is:

```gitignore
data/raw/*
!data/raw/.gitkeep
!data/raw/example.md
```

### Protect Retrieval Quality

If retrieval logic changes, add tests or evals.

Do not replace hybrid retrieval with vector-only retrieval unless that is an explicit architectural decision.

## 21. Command Summary

Full local flow:

```powershell
docker compose up -d
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts\ingest_local.py
python scripts\query.py "What do my documents say?"
pytest
python -m app.evals.run_evals
```

API:

```powershell
uvicorn app.main:app --reload
```

Download embeddings:

```powershell
pip install -e ".[local-llm]"
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Download a GGUF model:

```powershell
python scripts\download_model.py --repo-id MODEL_REPO_ID --filename MODEL_NAME.gguf --target ./models/llm/model.gguf
```

Reset:

```powershell
python scripts\reset_db.py --yes-i-know
```

## 22. Final Summary

The system follows this flow:

```text
1. Add documents to data/raw.
2. Run ingestion.
3. Store documents, versions, chunks and embeddings.
4. Ask a question.
5. Search by meaning and by keywords.
6. Fuse retrieval results.
7. Check whether context is sufficient.
8. Generate an answer.
9. Return sources.
```

The guiding principle:

```text
Answers should be grounded in local evidence.
```
