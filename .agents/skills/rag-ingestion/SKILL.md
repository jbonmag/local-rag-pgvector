---
name: rag-ingestion
description: Guide local file ingestion, deduplication, versioning, chunking, and embedding generation.
---

# RAG Ingestion

Use this skill when changing ingestion.

- Load source files from `./data/raw`.
- Support TXT, Markdown, HTML, and PDF.
- Compute content hashes.
- Deduplicate unchanged documents.
- Version documents when content changes.
- Use deterministic chunking.
- Extract useful metadata.
- Generate embeddings in batches.
- Record ingestion errors without logging sensitive full document content.
