"""initial local rag schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-06
"""

import os

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def embedding_dimension() -> int:
    value = os.getenv("EMBEDDING_DIMENSION", "384")
    try:
        dimension = int(value)
    except ValueError as exc:
        raise RuntimeError(f"EMBEDDING_DIMENSION must be an integer, got {value!r}") from exc
    if dimension <= 0:
        raise RuntimeError("EMBEDDING_DIMENSION must be positive")
    return dimension


def upgrade() -> None:
    dim = embedding_dimension()
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("source_uri", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "source_uri", name="uq_documents_tenant_source"),
    )
    op.create_index("ix_documents_tenant_id", "documents", ["tenant_id"])

    op.create_table(
        "document_versions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "document_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("documents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("version_label", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("document_id", "content_hash", name="uq_doc_version_hash"),
    )

    op.execute(
        """
        CREATE TABLE chunks (
            id uuid PRIMARY KEY,
            document_version_id uuid NOT NULL REFERENCES document_versions(id) ON DELETE CASCADE,
            tenant_id text NOT NULL,
            chunk_index integer NOT NULL,
            content text NOT NULL,
            metadata jsonb NOT NULL,
            token_count integer NOT NULL,
            search_vector tsvector GENERATED ALWAYS AS
              (to_tsvector('simple', coalesce(content, ''))) STORED,
            CONSTRAINT uq_chunks_version_index UNIQUE (document_version_id, chunk_index)
        )
        """
    )
    op.create_index("ix_chunks_document_version_id", "chunks", ["document_version_id"])
    op.create_index("ix_chunks_tenant_id", "chunks", ["tenant_id"])
    op.create_index("ix_chunks_search_vector", "chunks", ["search_vector"], postgresql_using="gin")

    op.execute(
        f"""
        CREATE TABLE chunk_embeddings (
            chunk_id uuid PRIMARY KEY REFERENCES chunks(id) ON DELETE CASCADE,
            embedding vector({dim}) NOT NULL,
            embedding_model text NOT NULL,
            embedding_dimension integer NOT NULL,
            created_at timestamptz DEFAULT now()
        )
        """
    )
    op.execute(
        """
        CREATE INDEX ix_chunk_embeddings_embedding_hnsw
        ON chunk_embeddings USING hnsw (embedding vector_cosine_ops)
        """
    )

    op.create_table(
        "retrieval_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("tenant_id", sa.Text(), nullable=False),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("scores", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_retrieval_logs_tenant_id", "retrieval_logs", ["tenant_id"])

    op.create_table(
        "feedback",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "retrieval_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("retrieval_logs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("rating", sa.Integer(), nullable=True),
        sa.Column("comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )
    op.create_index("ix_feedback_retrieval_log_id", "feedback", ["retrieval_log_id"])


def downgrade() -> None:
    op.drop_index("ix_feedback_retrieval_log_id", table_name="feedback")
    op.drop_table("feedback")
    op.drop_index("ix_retrieval_logs_tenant_id", table_name="retrieval_logs")
    op.drop_table("retrieval_logs")
    op.execute("DROP INDEX IF EXISTS ix_chunk_embeddings_embedding_hnsw")
    op.execute("DROP TABLE IF EXISTS chunk_embeddings")
    op.drop_index("ix_chunks_search_vector", table_name="chunks")
    op.drop_index("ix_chunks_tenant_id", table_name="chunks")
    op.drop_index("ix_chunks_document_version_id", table_name="chunks")
    op.drop_table("chunks")
    op.drop_table("document_versions")
    op.drop_index("ix_documents_tenant_id", table_name="documents")
    op.drop_table("documents")
