# Local RAG with PostgreSQL and pgvector

Proyecto RAG local para Windows 11, pensado para funcionar offline despues de descargar los modelos. Usa FastAPI, PostgreSQL con pgvector, ingesta desde disco, busqueda hibrida, embeddings locales, generacion local opcional y respuestas con fuentes.

No usa Google Drive, OpenAI como backend principal, LM Studio ni Ollama. El modo por defecto es mock para que la API, la ingesta, la base de datos y los tests puedan probarse sin modelos pesados.

Para una explicacion paso a paso y muy detallada, lee [MANUAL_USO.md](MANUAL_USO.md).

## Arquitectura

- `data/raw`: documentos fuente locales. Soporta TXT, Markdown, HTML y PDF.
- `data/processed`: artefactos procesados locales. Esta carpeta esta ignorada por git.
- `models`: modelos descargados desde Hugging Face. Esta carpeta esta ignorada por git.
- PostgreSQL almacena documentos, versiones, chunks, embeddings, metadata, logs de retrieval y feedback.
- `pgvector` ejecuta busqueda vectorial.
- PostgreSQL full-text search ejecuta busqueda keyword con `tsvector`.
- Reciprocal Rank Fusion combina resultados vectoriales y keyword.
- FastAPI expone `/health`, `/ingest/local` y `/query`.

## Requisitos

- Windows 11
- Docker Desktop
- Python 3.11+
- PowerShell

## Arranque rapido: modo A, mock completo

Este modo no requiere modelos reales.

```powershell
docker compose up -d
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts\ingest_local.py
python scripts\query.py "¿Que dicen mis documentos sobre X?"
pytest
python -m app.evals.run_evals
```

Para arrancar la API:

```powershell
uvicorn app.main:app --reload
```

Endpoints:

- `GET /health`
- `POST /ingest/local`
- `POST /query`

## Configuracion

Copia `.env.example` a `.env` y ajusta valores si hace falta.

```powershell
Copy-Item .env.example .env
```

Valores principales:

```env
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/ragdb
RAG_DEFAULT_TENANT_ID=local
RAG_MIN_VECTOR_SCORE=0.75
EMBEDDINGS_BACKEND=mock
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

## PostgreSQL y migraciones

PostgreSQL corre con Docker Compose usando la imagen `pgvector/pgvector:pg16`.

```powershell
docker compose up -d
alembic upgrade head
```

La migracion inicial habilita `CREATE EXTENSION vector`, crea la columna vectorial con la dimension de `EMBEDDING_DIMENSION`, crea un indice HNSW para embeddings y un indice GIN para full-text search.

Importante: cambiar `EMBEDDING_DIMENSION` requiere recrear o migrar embeddings y la columna vectorial. El valor por defecto es `384`, adecuado para `intfloat/multilingual-e5-small`.

## Ingesta local

Coloca documentos en `data/raw`:

```text
data/raw/manual.md
data/raw/notas.txt
data/raw/pagina.html
data/raw/informe.pdf
```

Ejecuta:

```powershell
python scripts\ingest_local.py
```

La ingesta:

- calcula hash SHA-256 del contenido extraido;
- crea o reutiliza `documents`;
- crea `document_versions` solo si cambia el contenido;
- hace chunking determinista;
- genera embeddings en batch;
- evita duplicar versiones sin cambios.

## Consulta

```powershell
python scripts\query.py "¿Que dicen mis documentos sobre X?"
```

Contrato de respuesta:

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

Si no hay contexto suficiente, `sufficient_context` sera `false` y `sources` puede estar vacio.

## Busqueda hibrida

`app/retrieval/hybrid.py` ejecuta:

- vector search con pgvector;
- keyword search con PostgreSQL full-text search;
- fusion con Reciprocal Rank Fusion;
- logging en `retrieval_logs`.
- umbral basico `RAG_MIN_VECTOR_SCORE` para no tratar recuperaciones vectoriales debiles como contexto suficiente. Los matches keyword siguen contando como contexto suficiente.

No se debe reemplazar esto por vector-only retrieval salvo peticion explicita.

## Modo B: embeddings locales + generacion mock

Instala dependencias opcionales:

```powershell
pip install -e ".[local-llm]"
```

Descarga embeddings:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Configura:

```env
EMBEDDINGS_BACKEND=sentence_transformers
EMBEDDING_MODEL_PATH=./models/embeddings/multilingual-e5-small
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

Con `ALLOW_MODEL_DOWNLOAD=false`, la inferencia no intenta descargar nada. Si la carpeta no existe, el error indica como corregirlo.

## Modo C: embeddings locales + LLM local

### llama-cpp-python con GGUF

Descarga un GGUF concreto:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --filename NOMBRE_DEL_MODELO.gguf --target ./models/llm/model.gguf
```

Configura:

```env
LOCAL_LLM_BACKEND=llama_cpp
LOCAL_LLM_MODEL_PATH=./models/llm/model.gguf
LOCAL_LLM_CONTEXT_SIZE=4096
LOCAL_LLM_MAX_TOKENS=512
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_N_GPU_LAYERS=0
```

En Windows, `llama-cpp-python` puede requerir compiladores, CMake o wheels compatibles. No hace falta GPU; `LOCAL_LLM_N_GPU_LAYERS=0` usa CPU.

### transformers con carpeta local

Descarga un repositorio completo:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --target ./models/llm/NOMBRE
```

Configura:

```env
LOCAL_LLM_BACKEND=transformers
LOCAL_LLM_MODEL_PATH=./models/llm/NOMBRE
LOCAL_LLM_DEVICE=auto
LOCAL_LLM_DTYPE=auto
```

En Windows, `torch`, CUDA y `accelerate` pueden requerir instalacion especifica segun CPU/GPU. El proyecto no exige GPU.

## Descarga de modelos

El script usa `huggingface_hub`, no scraping, y respeta `HF_TOKEN` si esta definido.

Repositorio completo:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Archivo GGUF:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --filename NOMBRE_DEL_MODELO.gguf --target ./models/llm/model.gguf
```

`models/` esta ignorado por git.

## Tests y evals

```powershell
pytest
python -m app.evals.run_evals
```

Los tests unitarios cubren hashing, chunking, RRF, embeddings mock, seleccion de backend local y contrato de respuesta. Las evals basicas usan `app/evals/golden.jsonl`; requieren base de datos migrada y contenido ingerido para los positivos.

## Reset de datos

El reset exige una bandera explicita:

```powershell
python scripts\reset_db.py --yes-i-know
```

