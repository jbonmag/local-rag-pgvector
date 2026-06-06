from collections import defaultdict


def reciprocal_rank_fusion(
    ranked_lists: list[list[str]], k: int = 60, top_k: int | None = None
) -> list[tuple[str, float]]:
    scores: dict[str, float] = defaultdict(float)
    for ranked in ranked_lists:
        for rank, item_id in enumerate(ranked, start=1):
            scores[item_id] += 1.0 / (k + rank)

    fused = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
    return fused[:top_k] if top_k is not None else fused
