from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ingestion.chunking import chunk_text
from app.ingestion.hashing import content_hash
from app.ingestion.loaders import iter_supported_files, load_file, source_uri_for
from app.llm.local_embeddings import LocalEmbeddings
from app.models import Chunk, ChunkEmbedding, Document, DocumentVersion
from app.schemas import IngestLocalResponse


def ingest_local(db: Session, raw_dir: Path, tenant_id: str) -> IngestLocalResponse:
    raw_dir = Path(raw_dir)
    files = iter_supported_files(raw_dir)
    embeddings = LocalEmbeddings()
    stats: dict[str, Any] = {
        "tenant_id": tenant_id,
        "files_seen": len(files),
        "documents_created": 0,
        "versions_created": 0,
        "chunks_created": 0,
        "embeddings_created": 0,
        "skipped_unchanged": 0,
        "errors": [],
    }

    for path in files:
        file_stats = {
            "documents_created": 0,
            "versions_created": 0,
            "chunks_created": 0,
            "embeddings_created": 0,
            "skipped_unchanged": 0,
        }
        try:
            loaded = load_file(path, raw_dir)
            if not loaded.text.strip():
                stats["errors"].append({"path": str(path), "error": "No extractable text"})
                continue

            source_uri = source_uri_for(path, raw_dir)
            doc_hash = content_hash(loaded.text)
            document = _get_or_create_document(db, tenant_id, source_uri, loaded, file_stats)

            version = db.scalar(
                select(DocumentVersion).where(
                    DocumentVersion.document_id == document.id,
                    DocumentVersion.content_hash == doc_hash,
                )
            )
            if version is None:
                version = DocumentVersion(
                    document_id=document.id,
                    content_hash=doc_hash,
                    version_label=doc_hash[:12],
                )
                db.add(version)
                db.flush()
                file_stats["versions_created"] += 1
            elif _version_has_chunks(db, version.id):
                file_stats["skipped_unchanged"] += 1
                _merge_stats(stats, file_stats)
                continue

            text_chunks = chunk_text(loaded.text)
            chunk_rows = [
                Chunk(
                    document_version_id=version.id,
                    tenant_id=tenant_id,
                    chunk_index=chunk.index,
                    content=chunk.content,
                    metadata_={"source_uri": source_uri, "content_hash": doc_hash},
                    token_count=chunk.token_count,
                )
                for chunk in text_chunks
            ]
            db.add_all(chunk_rows)
            db.flush()
            file_stats["chunks_created"] += len(chunk_rows)

            vectors = embeddings.embed_texts([chunk.content for chunk in chunk_rows])
            db.add_all(
                ChunkEmbedding(
                    chunk_id=chunk.id,
                    embedding=vector,
                    embedding_model=embeddings.model_name,
                    embedding_dimension=embeddings.dimension,
                )
                for chunk, vector in zip(chunk_rows, vectors, strict=True)
            )
            file_stats["embeddings_created"] += len(vectors)
            db.commit()
            _merge_stats(stats, file_stats)
        except Exception as exc:
            db.rollback()
            stats["errors"].append({"path": str(path), "error": str(exc)})

    return IngestLocalResponse(**stats)


def _get_or_create_document(
    db: Session, tenant_id: str, source_uri: str, loaded: Any, stats: dict[str, Any]
) -> Document:
    document = db.scalar(
        select(Document).where(Document.tenant_id == tenant_id, Document.source_uri == source_uri)
    )
    if document is not None:
        return document

    document = Document(
        tenant_id=tenant_id,
        source_type=loaded.source_type,
        source_uri=source_uri,
        title=loaded.title,
        metadata_=loaded.metadata,
    )
    db.add(document)
    db.flush()
    stats["documents_created"] += 1
    return document


def _version_has_chunks(db: Session, version_id) -> bool:
    return (
        db.scalar(select(Chunk.id).where(Chunk.document_version_id == version_id).limit(1))
        is not None
    )


def _merge_stats(stats: dict[str, Any], file_stats: dict[str, int]) -> None:
    for key, value in file_stats.items():
        stats[key] += value
