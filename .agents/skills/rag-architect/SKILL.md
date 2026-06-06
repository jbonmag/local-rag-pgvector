---
name: rag-architect
description: Review and guide the architecture of this local RAG system.
---

# RAG Architect

Use this skill when changing the RAG architecture.

- Avoid vector-only retrieval as the final retrieval strategy.
- Require hybrid retrieval with vector search plus PostgreSQL full-text search.
- Require traceability from answer to chunk, document version, and source file.
- Require citations in every answer.
- Keep tenant and permission boundaries explicit, even if only one local tenant is used initially.
- Design retrieval, generation, and ingestion so they can be evaluated from the start.
- Prefer small, composable modules over heavy frameworks.
