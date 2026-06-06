from app.retrieval.hybrid import RetrievedChunk, _has_sufficient_context


def _chunk(keyword_rank=None, vector_score=None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id="chunk",
        document_id="doc",
        title="Title",
        source_uri="example.md",
        content="content",
        keyword_rank=keyword_rank,
        vector_score=vector_score,
    )


def test_keyword_match_is_sufficient_context() -> None:
    assert _has_sufficient_context([_chunk(keyword_rank=1, vector_score=0.01)])


def test_weak_vector_only_match_is_not_sufficient_context() -> None:
    assert not _has_sufficient_context([_chunk(vector_score=0.01)])


def test_strong_vector_only_match_is_sufficient_context() -> None:
    assert _has_sufficient_context([_chunk(vector_score=0.9)])
