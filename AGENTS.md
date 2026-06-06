# Repo Rules

This project implements a local RAG system with PostgreSQL, pgvector, hybrid retrieval, citations, local models, and evaluation.

- Do not implement vector-only retrieval unless explicitly requested.
- Keep raw source files outside PostgreSQL.
- Store documents, versions, chunks, embeddings, metadata, retrieval logs, and feedback in PostgreSQL.
- Every RAG answer must include sources.
- Every retrieval change must include tests or evals.
- Keep code simple and maintainable.
- Do not mix tenants or permission scopes.
- Do not log secrets or complete sensitive content.
- Do not use OpenAI as the primary backend.
- Do not use LM Studio.
- Do not use Ollama.
- Do not commit or upload local models to the repository.
