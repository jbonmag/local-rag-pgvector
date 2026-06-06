---
name: rag-answer-contract
description: Define and protect the stable JSON response contract for RAG answers.
---

# RAG Answer Contract

Use this skill when changing query responses.

- Return a stable JSON object.
- Include `answer`.
- Include `sources`.
- Include `sufficient_context`.
- Do not fabricate answers when context is insufficient.
- Separate answer text from evidence metadata.
- Do not expose internal prompts.
