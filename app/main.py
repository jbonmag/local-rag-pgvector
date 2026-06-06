from fastapi import FastAPI

from app.api.ingest import router as ingest_router
from app.api.query import router as query_router
from app.schemas import HealthResponse

app = FastAPI(title="Local RAG pgvector", version="0.1.0")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


app.include_router(ingest_router)
app.include_router(query_router)
