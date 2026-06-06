from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str


class IngestLocalRequest(BaseModel):
    tenant_id: str | None = None


class IngestLocalResponse(BaseModel):
    tenant_id: str
    files_seen: int
    documents_created: int
    versions_created: int
    chunks_created: int
    embeddings_created: int
    skipped_unchanged: int
    errors: list[dict] = Field(default_factory=list)


class QueryRequest(BaseModel):
    question: str = Field(min_length=1)
    tenant_id: str | None = None
    top_k: int = Field(default=5, ge=1, le=30)


class Source(BaseModel):
    document_id: str
    chunk_id: str
    title: str | None
    source_uri: str
    snippet: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    retrieval_log_id: str | None
    sufficient_context: bool
