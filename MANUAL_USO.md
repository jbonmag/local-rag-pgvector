# Manual de uso del RAG local

Este manual explica, paso a paso y con lenguaje sencillo, como usar y entender este proyecto RAG local.

La idea es que puedas leerlo aunque no seas experto en inteligencia artificial, bases de datos o servidores. Si entiendes como se guarda informacion en carpetas y como se hacen preguntas a un buscador, puedes entender este sistema.

## 1. Que es este proyecto

Este proyecto es un RAG local.

RAG significa "Retrieval Augmented Generation". En castellano sencillo:

- "Retrieval" significa buscar informacion.
- "Augmented" significa mejorar o apoyar.
- "Generation" significa generar una respuesta.

O sea: el sistema primero busca informacion en tus documentos y despues usa esa informacion para escribir una respuesta.

No es un chatbot que responde solo con lo que ya sabe. Es un sistema que intenta responder usando tus documentos locales.

## 2. La idea explicada con una biblioteca

Imagina que tienes una biblioteca en casa:

1. Metes libros, apuntes y PDFs en una estanteria.
2. Haces una pregunta.
3. Alguien busca las paginas que parecen hablar de tu pregunta.
4. Lee esas paginas.
5. Te responde usando solo esas paginas.
6. Te dice de que libro o pagina ha sacado la informacion.

Este proyecto hace lo mismo, pero con codigo:

1. Tus documentos viven en `data/raw`.
2. El sistema lee esos documentos.
3. Los divide en trozos pequenos llamados chunks.
4. Guarda esos chunks en PostgreSQL.
5. Calcula embeddings para poder buscar por significado.
6. Tambien usa busqueda por palabras clave.
7. Junta ambos tipos de busqueda.
8. Genera una respuesta.
9. Devuelve fuentes y citas.

## 3. Que NO usa este proyecto

Este proyecto esta disenado para trabajar de forma local y offline despues de descargar modelos.

No usa:

- Google Drive.
- OpenAI como backend principal.
- LM Studio.
- Ollama.
- Servidores externos de inferencia.

Por defecto usa modo `mock`, que sirve para probar todo sin descargar ningun modelo pesado.

## 4. Que piezas tiene el sistema

El proyecto tiene estas piezas principales:

```text
FastAPI
PostgreSQL
pgvector
Ingesta local
Embeddings locales
Busqueda hibrida
Generacion local o mock
Evaluaciones
Tests
Skills locales de Codex
```

Ahora las explicamos una por una.

### 4.1 FastAPI

FastAPI es el pequeno servidor web del proyecto.

Sirve para exponer endpoints, que son rutas a las que puedes llamar.

Endpoints incluidos:

- `GET /health`: comprueba que la API responde.
- `POST /ingest/local`: ingiere documentos desde `data/raw`.
- `POST /query`: hace una pregunta al RAG.

### 4.2 PostgreSQL

PostgreSQL es la base de datos.

Aqui se guardan:

- documentos registrados;
- versiones de documentos;
- chunks;
- embeddings;
- logs de busqueda;
- feedback.

Importante: los archivos originales no se guardan dentro de PostgreSQL. Se quedan en disco, en `data/raw`.

### 4.3 pgvector

pgvector es una extension de PostgreSQL.

Permite guardar vectores y buscar vectores parecidos.

Un vector es una lista de numeros. En este proyecto, un embedding es un vector.

Ejemplo simple:

```text
[0.12, -0.03, 0.44, ...]
```

En la practica, el vector representa el significado de un texto.

### 4.4 Ingesta local

La ingesta es el proceso de leer archivos desde `data/raw`.

El sistema soporta:

- `.txt`
- `.md`
- `.markdown`
- `.html`
- `.htm`
- `.pdf`

La ingesta hace esto:

1. Busca archivos soportados.
2. Extrae texto.
3. Calcula un hash del contenido.
4. Comprueba si el documento ya existe.
5. Comprueba si esa version ya existe.
6. Divide el texto en chunks.
7. Calcula embeddings.
8. Guarda todo en PostgreSQL.

### 4.5 Embeddings locales

Un embedding convierte texto en numeros.

Sirve para que el sistema pueda buscar textos parecidos aunque no tengan exactamente las mismas palabras.

Ejemplo:

```text
Pregunta: "normas internas"
Documento: "politicas internas"
```

Aunque no sean las mismas palabras, el sistema puede entender que estan relacionadas.

Este proyecto soporta dos backends de embeddings:

- `mock`
- `sentence_transformers`

El backend `mock` no necesita modelos reales. Es determinista y sirve para desarrollo y tests.

El backend `sentence_transformers` usa modelos locales descargados desde Hugging Face.

### 4.6 Busqueda hibrida

Este proyecto no usa solo busqueda vectorial.

Usa busqueda hibrida:

```text
Busqueda hibrida = busqueda vectorial + busqueda por palabras clave
```

La busqueda vectorial encuentra textos parecidos por significado.

La busqueda por palabras clave encuentra textos que contienen palabras importantes de la pregunta.

Despues se combinan con RRF.

RRF significa "Reciprocal Rank Fusion". Es una tecnica para unir listas de resultados.

### 4.7 Generacion local

La generacion es la parte que escribe la respuesta final.

Este proyecto soporta:

- `mock`
- `llama_cpp`
- `transformers`

El backend `mock` siempre funciona y no necesita modelo real.

El backend `llama_cpp` carga un archivo GGUF local con `llama-cpp-python`.

El backend `transformers` carga una carpeta local de Hugging Face con `transformers`.

## 5. Estructura de carpetas

Esta es la estructura importante:

```text
.
├─ AGENTS.md
├─ README.md
├─ MANUAL_USO.md
├─ .env.example
├─ docker-compose.yml
├─ pyproject.toml
├─ alembic.ini
├─ app/
├─ migrations/
├─ scripts/
├─ tests/
├─ data/
│  ├─ raw/
│  └─ processed/
├─ models/
│  ├─ llm/
│  └─ embeddings/
└─ .agents/
   └─ skills/
```

### 5.1 `data/raw`

Aqui metes tus documentos originales.

Ejemplo:

```text
data/raw/manual_empresa.md
data/raw/apuntes_historia.pdf
data/raw/notas.txt
```

En este repo publico, `data/raw/*` esta ignorado por git salvo `.gitkeep` y `example.md`.

Eso evita subir documentos privados por accidente.

### 5.2 `data/processed`

Aqui pueden vivir archivos procesados.

Esta carpeta esta ignorada por git.

### 5.3 `models`

Aqui van los modelos descargados desde Hugging Face.

Esta carpeta esta ignorada por git.

No subas modelos al repositorio.

### 5.4 `app`

Aqui esta el codigo principal.

Subcarpetas importantes:

- `app/api`: endpoints FastAPI.
- `app/ingestion`: carga de documentos, hashing y chunking.
- `app/retrieval`: busqueda hibrida.
- `app/llm`: embeddings y generacion local.
- `app/evals`: evaluaciones basicas.

### 5.5 `migrations`

Aqui estan las migraciones de Alembic.

Alembic sirve para crear y cambiar tablas de PostgreSQL de forma controlada.

### 5.6 `scripts`

Aqui hay comandos utiles:

- `download_model.py`
- `ingest_local.py`
- `query.py`
- `reset_db.py`

### 5.7 `tests`

Aqui estan los tests.

Sirven para comprobar que piezas importantes siguen funcionando.

### 5.8 `.agents/skills`

Aqui estan las skills locales de Codex para este repo.

Sirven como instrucciones especializadas para mantener el proyecto bien disenado.

## 6. Requisitos antes de empezar

Necesitas:

- Windows 11.
- Docker Desktop.
- Python 3.11 o superior.
- PowerShell.
- Conexion a internet solo para instalar dependencias o descargar modelos.

Despues de descargar modelos, el sistema puede funcionar offline.

## 7. Primer arranque paso a paso

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\jbonm\Documents\MIS PROYECTOS\RAG"
```

### Paso 1: levantar PostgreSQL

Ejecuta:

```powershell
docker compose up -d
```

Esto arranca PostgreSQL con pgvector.

Puedes imaginarlo como encender la base de datos.

### Paso 2: crear entorno virtual

Si no existe `.venv`, crea uno:

```powershell
python -m venv .venv
```

Activalo:

```powershell
.venv\Scripts\activate
```

Cuando esta activo, los paquetes Python se instalan dentro del proyecto y no ensucian todo Windows.

### Paso 3: instalar dependencias

Para modo basico y tests:

```powershell
pip install -e ".[dev]"
```

Esto instala:

- FastAPI.
- SQLAlchemy.
- Alembic.
- psycopg.
- pgvector.
- pypdf.
- beautifulsoup4.
- pytest.
- ruff.

No instala modelos pesados.

### Paso 4: crear tablas

Ejecuta:

```powershell
alembic upgrade head
```

Esto crea las tablas en PostgreSQL.

Tambien habilita la extension `vector`.

### Paso 5: meter documentos

Mete documentos en:

```text
data/raw
```

Ejemplo:

```text
data/raw/apuntes.md
```

### Paso 6: ingerir documentos

Ejecuta:

```powershell
python scripts\ingest_local.py
```

Salida esperada:

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

Si lo ejecutas otra vez sin cambiar el documento, debe ser idempotente:

```json
{
  "documents_created": 0,
  "versions_created": 0,
  "chunks_created": 0,
  "embeddings_created": 0,
  "skipped_unchanged": 1
}
```

Eso significa que no duplico informacion.

### Paso 7: hacer una pregunta

Ejecuta:

```powershell
python scripts\query.py "¿Que dicen mis documentos sobre politicas internas?"
```

Respuesta esperada:

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

La parte mas importante:

- `answer`: la respuesta.
- `sources`: de donde saco la informacion.
- `sufficient_context`: si habia contexto suficiente.

## 8. Como arrancar la API

Puedes levantar el servidor FastAPI con:

```powershell
uvicorn app.main:app --reload
```

Por defecto se abre en:

```text
http://127.0.0.1:8000
```

Documentacion automatica:

```text
http://127.0.0.1:8000/docs
```

### 8.1 Probar salud

Endpoint:

```text
GET /health
```

Respuesta:

```json
{
  "status": "ok"
}
```

### 8.2 Ingerir desde API

Endpoint:

```text
POST /ingest/local
```

Cuerpo opcional:

```json
{
  "tenant_id": "local"
}
```

### 8.3 Preguntar desde API

Endpoint:

```text
POST /query
```

Cuerpo:

```json
{
  "question": "¿Que dicen mis documentos sobre politicas internas?",
  "tenant_id": "local",
  "top_k": 5
}
```

## 9. Que pasa por dentro cuando ingieres un documento

Supongamos que metes este archivo:

```text
data/raw/apuntes.md
```

El sistema hace esto:

### 9.1 Encuentra el archivo

Busca archivos soportados dentro de `data/raw`.

Si encuentra un `.md`, lo procesa como Markdown.

### 9.2 Extrae texto

Lee el contenido.

Para PDF usa `pypdf`.

Para HTML usa `beautifulsoup4`.

### 9.3 Calcula hash

Calcula un SHA-256 del texto.

Un hash es como una huella digital del contenido.

Si el texto cambia, el hash cambia.

Si el texto no cambia, el hash es el mismo.

Esto permite versionar documentos.

### 9.4 Crea o reutiliza `documents`

La tabla `documents` representa el documento como fuente.

Ejemplo:

```text
source_uri = apuntes.md
title = apuntes
source_type = markdown
```

### 9.5 Crea o reutiliza `document_versions`

La tabla `document_versions` representa una version concreta del documento.

Si modificas el archivo, se crea una nueva version.

Si no lo modificas, se reutiliza la version existente.

### 9.6 Crea chunks

El sistema divide el texto en trozos.

Estos trozos se llaman chunks.

Ejemplo:

```text
Chunk 0: primeras 300 palabras
Chunk 1: siguientes 300 palabras con solape
Chunk 2: siguientes 300 palabras con solape
```

El solape sirve para no cortar ideas por la mitad.

### 9.7 Calcula embeddings

Cada chunk se convierte en un vector.

Ese vector se guarda en `chunk_embeddings`.

### 9.8 Guarda todo

PostgreSQL queda con:

- documento;
- version;
- chunks;
- embeddings.

## 10. Tablas de la base de datos

### 10.1 `documents`

Guarda una fuente documental.

Campos importantes:

- `id`: identificador unico.
- `tenant_id`: ambito o cliente.
- `source_type`: tipo de fuente.
- `source_uri`: ruta del archivo dentro de `data/raw`.
- `title`: titulo.
- `metadata`: informacion extra.
- `created_at`: fecha de creacion.

### 10.2 `document_versions`

Guarda versiones de documentos.

Campos importantes:

- `id`: identificador de version.
- `document_id`: documento al que pertenece.
- `content_hash`: hash SHA-256.
- `version_label`: etiqueta de version.
- `created_at`: fecha.

Regla importante:

```text
unique(document_id, content_hash)
```

Esto evita duplicar la misma version.

### 10.3 `chunks`

Guarda trozos de texto.

Campos importantes:

- `id`: identificador del chunk.
- `document_version_id`: version documental.
- `tenant_id`: ambito.
- `chunk_index`: numero del chunk.
- `content`: texto del chunk.
- `metadata`: informacion extra.
- `token_count`: estimacion de tokens.
- `search_vector`: columna para full-text search.

`search_vector` es generada por PostgreSQL.

### 10.4 `chunk_embeddings`

Guarda embeddings.

Campos importantes:

- `chunk_id`: chunk asociado.
- `embedding`: vector.
- `embedding_model`: modelo usado.
- `embedding_dimension`: dimension del vector.
- `created_at`: fecha.

La dimension por defecto es `384`.

### 10.5 `retrieval_logs`

Guarda registros de busqueda.

Sirve para saber que chunks se recuperaron para una pregunta.

Campos importantes:

- `query`: pregunta.
- `tenant_id`: ambito.
- `retrieved_chunk_ids`: chunks recuperados.
- `scores`: puntuaciones.

### 10.6 `feedback`

Guarda feedback humano.

Campos importantes:

- `retrieval_log_id`: busqueda evaluada.
- `rating`: puntuacion.
- `comment`: comentario.

## 11. Como funciona la busqueda hibrida

Cuando preguntas algo, el sistema hace dos busquedas.

### 11.1 Busqueda vectorial

1. Convierte tu pregunta en embedding.
2. Compara ese embedding con embeddings de chunks.
3. Encuentra chunks cercanos por significado.

Ventaja:

- Puede encontrar textos parecidos aunque las palabras no sean identicas.

Riesgo:

- A veces puede traer algo parecido pero no realmente suficiente.

Por eso hay un umbral:

```env
RAG_MIN_VECTOR_SCORE=0.75
```

### 11.2 Busqueda por palabras clave

1. Limpia la pregunta.
2. Quita palabras comunes.
3. Normaliza acentos.
4. Busca palabras importantes en `search_vector`.

Ejemplo:

```text
¿Cual es la contrasena privada del administrador?
```

Se convierte en algo parecido a:

```text
contrasena | privada | administrador
```

Si el documento no contiene esas palabras, no hay match keyword.

### 11.3 Fusion con RRF

Despues hay dos listas:

```text
Lista vectorial
Lista keyword
```

RRF combina las dos.

Si un chunk aparece bien colocado en ambas listas, suele quedar arriba.

Si aparece en una sola, tambien puede salir, pero con menos fuerza.

### 11.4 Resultado final

El sistema devuelve los mejores chunks.

Cada chunk recuperado incluye:

- `chunk_id`
- `document_id`
- `title`
- `source_uri`
- `content`
- puntuaciones

## 12. Como decide si hay contexto suficiente

El sistema no debe inventar.

Por eso usa una regla basica:

Hay contexto suficiente si:

- hay match keyword; o
- hay match vectorial con puntuacion alta.

Si no se cumple, responde:

```text
No hay informacion suficiente en los documentos locales para responder.
```

Y devuelve:

```json
{
  "sources": [],
  "sufficient_context": false
}
```

## 13. Contrato de respuesta

Todas las respuestas de `/query` siguen este formato:

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

### 13.1 `answer`

Es la respuesta escrita.

### 13.2 `sources`

Es la lista de fuentes.

Cada fuente muestra de donde salio el contexto.

Esto es obligatorio cuando hay respuesta con contexto.

### 13.3 `retrieval_log_id`

Es el identificador del log de busqueda.

Sirve para revisar despues que paso.

### 13.4 `sufficient_context`

Indica si habia suficiente informacion.

Si es `false`, no deberias confiar en una respuesta larga.

## 14. Modos de uso

El proyecto tiene tres modos principales.

## 14.1 Modo A: mock completo

Este es el modo por defecto.

No requiere modelos.

Configuracion:

```env
EMBEDDINGS_BACKEND=mock
LOCAL_LLM_BACKEND=mock
```

Sirve para:

- probar Docker;
- probar migraciones;
- probar ingesta;
- probar endpoints;
- ejecutar tests;
- entender el flujo.

No sirve para medir calidad real de IA.

## 14.2 Modo B: embeddings locales + generacion mock

Este modo usa embeddings reales, pero respuesta mock.

Configuracion:

```env
EMBEDDINGS_BACKEND=sentence_transformers
EMBEDDING_MODEL_PATH=./models/embeddings/multilingual-e5-small
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
LOCAL_LLM_BACKEND=mock
ALLOW_MODEL_DOWNLOAD=false
```

Sirve para:

- probar retrieval real;
- probar busqueda vectorial real;
- evitar cargar un LLM grande.

Descarga de modelo:

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

## 14.3 Modo C: embeddings locales + LLM local

Este modo usa embeddings reales y generacion real local.

Hay dos opciones:

- `llama_cpp`
- `transformers`

### Opcion C1: llama-cpp-python con GGUF

Configuracion:

```env
LOCAL_LLM_BACKEND=llama_cpp
LOCAL_LLM_MODEL_PATH=./models/llm/model.gguf
LOCAL_LLM_CONTEXT_SIZE=4096
LOCAL_LLM_MAX_TOKENS=512
LOCAL_LLM_TEMPERATURE=0.2
LOCAL_LLM_N_GPU_LAYERS=0
```

Descarga de GGUF:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --filename NOMBRE_DEL_MODELO.gguf --target ./models/llm/model.gguf
```

Instalacion de dependencias:

```powershell
pip install -e ".[local-llm]"
```

Nota para Windows:

`llama-cpp-python` puede necesitar compiladores o wheels compatibles. Si falla, revisa la documentacion del paquete segun tu CPU/GPU.

### Opcion C2: transformers con carpeta local

Configuracion:

```env
LOCAL_LLM_BACKEND=transformers
LOCAL_LLM_MODEL_PATH=./models/llm/NOMBRE_DEL_MODELO
LOCAL_LLM_DEVICE=auto
LOCAL_LLM_DTYPE=auto
```

Descarga:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --target ./models/llm/NOMBRE_DEL_MODELO
```

Nota para Windows:

`torch`, CUDA y `accelerate` pueden necesitar instalacion especial. No necesitas GPU para que el proyecto exista, pero algunos modelos seran lentos en CPU.

## 15. Variables de entorno

El archivo base es:

```text
.env.example
```

Puedes copiarlo:

```powershell
Copy-Item .env.example .env
```

### 15.1 Base de datos

```env
DATABASE_URL=postgresql+psycopg://rag:rag@localhost:5432/ragdb
```

Significa:

- usuario: `rag`
- password: `rag`
- host: `localhost`
- puerto: `5432`
- base de datos: `ragdb`

### 15.2 Tenant por defecto

```env
RAG_DEFAULT_TENANT_ID=local
```

Un tenant es un ambito.

Hoy solo usas `local`, pero el sistema esta preparado para no mezclar ambitos.

### 15.3 Umbral vectorial

```env
RAG_MIN_VECTOR_SCORE=0.75
```

Ayuda a evitar que una coincidencia vectorial floja se trate como suficiente.

### 15.4 Embeddings

```env
EMBEDDINGS_BACKEND=mock
EMBEDDING_MODEL_PATH=./models/embeddings/model
EMBEDDING_MODEL_NAME=intfloat/multilingual-e5-small
EMBEDDING_DIMENSION=384
```

Si cambias `EMBEDDING_DIMENSION`, necesitas recrear o migrar embeddings.

### 15.5 Descargas

```env
ALLOW_MODEL_DOWNLOAD=false
HF_TOKEN=
```

Si `ALLOW_MODEL_DOWNLOAD=false`, el sistema no intenta descargar modelos durante la inferencia.

Esto ayuda al modo offline.

## 16. Como descargar modelos desde Hugging Face

El script es:

```text
scripts/download_model.py
```

### 16.1 Descargar un repositorio completo

```powershell
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

### 16.2 Descargar un archivo GGUF

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --filename NOMBRE_DEL_MODELO.gguf --target ./models/llm/model.gguf
```

### 16.3 Token de Hugging Face

Si el modelo necesita autenticacion, define:

```env
HF_TOKEN=tu_token
```

No subas `.env` al repositorio.

## 17. Tests

Ejecuta:

```powershell
pytest
```

Los tests comprueban:

- hashing determinista;
- chunking;
- RRF;
- embeddings mock;
- errores claros si falta modelo local;
- contrato de respuesta;
- suficiencia de contexto;
- construccion de query keyword.

Si todo esta bien, veras algo parecido a:

```text
16 passed
```

## 18. Evals

Ejecuta:

```powershell
python -m app.evals.run_evals
```

Las evals usan:

```text
app/evals/golden.jsonl
```

Ese archivo contiene preguntas de prueba.

Hay ejemplos positivos y negativos.

Ejemplo positivo:

```text
Pregunta que deberia tener respuesta con fuentes.
```

Ejemplo negativo:

```text
Pregunta que no deberia responder si no hay contexto.
```

Salida esperada:

```json
{"total": 3, "passed": 3, "pass_rate": 1.0}
```

## 19. Como resetear la base de datos

Hay un script peligroso, por eso exige una bandera:

```powershell
python scripts\reset_db.py --yes-i-know
```

Esto borra los datos de las tablas RAG.

No borra tus archivos de `data/raw`.

## 20. Problemas comunes

### 20.1 Docker no arranca

Comprueba que Docker Desktop esta abierto.

Luego ejecuta:

```powershell
docker compose up -d
```

### 20.2 Alembic no conecta

Comprueba que PostgreSQL esta levantado.

Puedes mirar contenedores:

```powershell
docker ps
```

### 20.3 La ingesta no encuentra documentos

Comprueba que tus archivos estan dentro de:

```text
data/raw
```

Y que tienen extension soportada:

```text
.txt
.md
.markdown
.html
.htm
.pdf
```

### 20.4 La respuesta no tiene fuentes

Si `sufficient_context=false`, es normal que `sources` este vacio.

Eso significa que el sistema no encontro contexto suficiente.

### 20.5 Cambio el modelo de embeddings y falla

Si cambias la dimension, por ejemplo de `384` a `768`, debes recrear o migrar embeddings.

La columna vectorial de PostgreSQL se crea con una dimension concreta.

### 20.6 No tengo GPU

No pasa nada para modo mock.

Para modelos reales, CPU funciona, pero puede ser lento.

### 20.7 llama-cpp-python falla al instalar

En Windows puede necesitar compiladores o wheels especificos.

El proyecto no depende de `llama_cpp` en modo mock.

Puedes seguir trabajando con:

```env
LOCAL_LLM_BACKEND=mock
```

## 21. Buenas practicas

### 21.1 No subas modelos

`models/` esta ignorado por git.

Los modelos pueden pesar muchos GB.

### 21.2 No subas secretos

No subas:

- `.env`
- tokens;
- passwords;
- documentos sensibles.

### 21.3 Cuidado con `data/raw`

En este repo publico, los documentos reales de `data/raw` estan ignorados por defecto.

La regla usada en `.gitignore` es:

```gitignore
data/raw/*
!data/raw/.gitkeep
!data/raw/example.md
```

### 21.4 No cambies retrieval sin tests

Si cambias la busqueda, anade tests o evals.

Esto esta indicado en `AGENTS.md`.

### 21.5 No uses vector-only retrieval como solucion final

Este proyecto exige busqueda hibrida.

Vector-only puede parecer suficiente, pero pierde trazabilidad y puede traer contexto flojo.

## 22. Comandos principales resumidos

Arranque completo:

```powershell
docker compose up -d
.venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
python scripts\ingest_local.py
python scripts\query.py "¿Que dicen mis documentos?"
pytest
python -m app.evals.run_evals
```

API:

```powershell
uvicorn app.main:app --reload
```

Descargar embeddings:

```powershell
pip install -e ".[local-llm]"
python scripts\download_model.py --repo-id intfloat/multilingual-e5-small --target ./models/embeddings/multilingual-e5-small
```

Descargar GGUF:

```powershell
python scripts\download_model.py --repo-id REPO_ID_DEL_MODELO --filename NOMBRE_DEL_MODELO.gguf --target ./models/llm/model.gguf
```

Reset:

```powershell
python scripts\reset_db.py --yes-i-know
```

## 23. Resumen mental del sistema

Si quieres recordarlo rapido:

```text
1. Metes documentos en data/raw.
2. Ejecutas ingesta.
3. El sistema crea documentos, versiones, chunks y embeddings.
4. Haces una pregunta.
5. El sistema busca por significado y por palabras.
6. Fusiona resultados.
7. Decide si hay contexto suficiente.
8. Genera respuesta.
9. Devuelve fuentes.
```

La regla de oro:

```text
Sin fuentes, no hay respuesta confiable.
```

Este proyecto esta hecho para que esa regla sea parte del sistema desde el principio.
