---
name: pgvector-postgres
description: Guide PostgreSQL and pgvector schema, migrations, and retrieval queries.
---

# pgvector PostgreSQL

Use this skill when changing database schema or retrieval SQL.

- Create schema changes through SQL or Alembic migrations.
- Enable the `vector` extension through migration.
- Use HNSW indexes when data volume justifies it.
- Implement PostgreSQL full-text search alongside vector search.
- Review important retrieval queries with `EXPLAIN ANALYZE`.
- Apply tenant and permission filters before ranking.
- Store `embedding_model` and `embedding_dimension` with embeddings.
- Do not hardcode embedding dimensions in application logic; read them from configuration.
