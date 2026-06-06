import re
import unicodedata
from dataclasses import dataclass
from typing import Protocol

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.llm.local_embeddings import LocalEmbeddings
from app.llm.prompts import DEFAULT_SYSTEM_PROMPT
from app.models import RetrievalLog
from app.retrieval.prompts import INSUFFICIENT_CONTEXT_ANSWER
from app.retrieval.rrf import reciprocal_rank_fusion
from app.schemas import QueryResponse, Source

STOPWORDS = {
    "a",
    "al",
    "de",
    "del",
    "el",
    "en",
    "la",
    "las",
    "lo",
    "los",
    "que",
    "un",
    "una",
    "unas",
    "unos",
    "sobre",
    "cual",
    "cuál",
    "como",
    "qué",
    "porque",
    "para",
    "por",
    "con",
}


class GeneratorProtocol(Protocol):
    def generate(
        self, question: str, contexts: list[dict], system_prompt: str | None = None
    ) -> str:
        ...


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    document_id: str
    title: str | None
    source_uri: str
    content: str
    vector_rank: int | None = None
    keyword_rank: int | None = None
    vector_score: float | None = None
    keyword_score: float | None = None
    fused_score: float = 0.0


def hybrid_search(
    db: Session,
    query: str,
    tenant_id: str,
    top_k: int = 5,
    top_k_vector: int | None = None,
    top_k_keyword: int | None = None,
) -> list[RetrievedChunk]:
    settings = get_settings()
    top_k_vector = top_k_vector or max(top_k * 3, 10)
    top_k_keyword = top_k_keyword or max(top_k * 3, 10)

    embedding_client = LocalEmbeddings(settings)
    query_embedding = embedding_client.embed_query(query)
    vector_rows = _vector_search(db, query_embedding, tenant_id, top_k_vector)
    keyword_rows = _keyword_search(db, query, tenant_id, top_k_keyword)

    vector_ids = [row["chunk_id"] for row in vector_rows]
    keyword_ids = [row["chunk_id"] for row in keyword_rows]
    fused = reciprocal_rank_fusion([vector_ids, keyword_ids], top_k=top_k)

    by_id = {row["chunk_id"]: row for row in vector_rows + keyword_rows}
    vector_rank = {chunk_id: idx for idx, chunk_id in enumerate(vector_ids, start=1)}
    keyword_rank = {chunk_id: idx for idx, chunk_id in enumerate(keyword_ids, start=1)}
    vector_score = {row["chunk_id"]: row.get("vector_score") for row in vector_rows}
    keyword_score = {row["chunk_id"]: row.get("keyword_score") for row in keyword_rows}

    return [
        RetrievedChunk(
            chunk_id=chunk_id,
            document_id=by_id[chunk_id]["document_id"],
            title=by_id[chunk_id].get("title"),
            source_uri=by_id[chunk_id]["source_uri"],
            content=by_id[chunk_id]["content"],
            vector_rank=vector_rank.get(chunk_id),
            keyword_rank=keyword_rank.get(chunk_id),
            vector_score=vector_score.get(chunk_id),
            keyword_score=keyword_score.get(chunk_id),
            fused_score=fused_score,
        )
        for chunk_id, fused_score in fused
        if chunk_id in by_id
    ]


def answer_question(
    db: Session,
    question: str,
    tenant_id: str,
    top_k: int,
    generator: GeneratorProtocol,
) -> QueryResponse:
    chunks = hybrid_search(db, question, tenant_id, top_k=top_k)
    sufficient_context = _has_sufficient_context(chunks)
    retrieval_log = RetrievalLog(
        query=question,
        tenant_id=tenant_id,
        retrieved_chunk_ids=[chunk.chunk_id for chunk in chunks],
        scores={
            chunk.chunk_id: {
                "fused": chunk.fused_score,
                "vector": chunk.vector_score,
                "keyword": chunk.keyword_score,
                "vector_rank": chunk.vector_rank,
                "keyword_rank": chunk.keyword_rank,
            }
            for chunk in chunks
        },
    )
    db.add(retrieval_log)
    db.commit()
    db.refresh(retrieval_log)

    if not sufficient_context:
        return QueryResponse(
            answer=INSUFFICIENT_CONTEXT_ANSWER,
            sources=[],
            retrieval_log_id=str(retrieval_log.id),
            sufficient_context=False,
        )

    sources = [
        Source(
            document_id=chunk.document_id,
            chunk_id=chunk.chunk_id,
            title=chunk.title,
            source_uri=chunk.source_uri,
            snippet=chunk.content[:400],
        )
        for chunk in chunks
    ]
    contexts = [
        {
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
            "title": chunk.title,
            "source_uri": chunk.source_uri,
            "content": chunk.content,
        }
        for chunk in chunks
    ]
    answer = generator.generate(question, contexts, DEFAULT_SYSTEM_PROMPT)
    return QueryResponse(
        answer=answer,
        sources=sources,
        retrieval_log_id=str(retrieval_log.id),
        sufficient_context=True,
    )


def rerank_noop(chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
    return chunks


def _has_sufficient_context(chunks: list[RetrievedChunk]) -> bool:
    if not chunks:
        return False
    min_vector_score = get_settings().rag_min_vector_score
    return any(
        chunk.keyword_rank is not None
        or (chunk.vector_score is not None and chunk.vector_score >= min_vector_score)
        for chunk in chunks
    )


def _vector_search(
    db: Session, query_embedding: list[float], tenant_id: str, limit: int
) -> list[dict]:
    rows = db.execute(
        text(
            """
            SELECT
              c.id::text AS chunk_id,
              d.id::text AS document_id,
              d.title AS title,
              d.source_uri AS source_uri,
              c.content AS content,
              1 - (ce.embedding <=> CAST(:embedding AS vector)) AS vector_score
            FROM chunks c
            JOIN chunk_embeddings ce ON ce.chunk_id = c.id
            JOIN document_versions dv ON dv.id = c.document_version_id
            JOIN documents d ON d.id = dv.document_id
            WHERE c.tenant_id = :tenant_id
              AND ce.embedding_dimension = :embedding_dimension
            ORDER BY ce.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        ),
        {
            "embedding": _format_vector(query_embedding),
            "tenant_id": tenant_id,
            "embedding_dimension": len(query_embedding),
            "limit": limit,
        },
    ).mappings()
    return [dict(row) for row in rows]


def _keyword_search(db: Session, query: str, tenant_id: str, limit: int) -> list[dict]:
    tsquery = _build_or_tsquery(query)
    if not tsquery:
        return []
    rows = db.execute(
        text(
            """
            SELECT
              c.id::text AS chunk_id,
              d.id::text AS document_id,
              d.title AS title,
              d.source_uri AS source_uri,
              c.content AS content,
              ts_rank_cd(c.search_vector, to_tsquery('simple', :tsquery)) AS keyword_score
            FROM chunks c
            JOIN document_versions dv ON dv.id = c.document_version_id
            JOIN documents d ON d.id = dv.document_id
            WHERE c.tenant_id = :tenant_id
              AND c.search_vector @@ to_tsquery('simple', :tsquery)
            ORDER BY keyword_score DESC
            LIMIT :limit
            """
        ),
        {"tsquery": tsquery, "tenant_id": tenant_id, "limit": limit},
    ).mappings()
    return [dict(row) for row in rows]


def _format_vector(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _build_or_tsquery(query: str) -> str:
    normalized = unicodedata.normalize("NFKD", query)
    ascii_query = "".join(char for char in normalized if not unicodedata.combining(char))
    tokens = re.findall(r"[A-Za-z0-9_]+", ascii_query.lower())
    unique_tokens = []
    for token in tokens:
        if len(token) <= 2 or token in STOPWORDS or token in unique_tokens:
            continue
        unique_tokens.append(token)
    return " | ".join(unique_tokens)
