from app.retrieval.rrf import reciprocal_rank_fusion


def test_rrf_fuses_ranked_lists() -> None:
    result = reciprocal_rank_fusion([["a", "b"], ["b", "c"]], top_k=3)
    assert result[0][0] == "b"
    assert {item for item, _ in result} == {"a", "b", "c"}
