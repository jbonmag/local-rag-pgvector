from app.schemas import QueryResponse, Source


def test_answer_contract_requires_sources_field() -> None:
    response = QueryResponse(
        answer="Respuesta",
        sources=[
            Source(
                document_id="doc",
                chunk_id="chunk",
                title="Titulo",
                source_uri="sample.txt",
                snippet="texto",
            )
        ],
        retrieval_log_id="log",
        sufficient_context=True,
    )
    dumped = response.model_dump()
    assert set(dumped) == {"answer", "sources", "retrieval_log_id", "sufficient_context"}
    assert dumped["sources"][0]["source_uri"] == "sample.txt"
