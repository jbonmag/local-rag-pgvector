from app.ingestion.chunking import chunk_text


def test_chunk_text_is_deterministic_and_overlaps() -> None:
    text = " ".join(f"w{i}" for i in range(12))
    chunks = chunk_text(text, max_tokens=5, overlap_tokens=2)
    assert [chunk.content for chunk in chunks] == [
        "w0 w1 w2 w3 w4",
        "w3 w4 w5 w6 w7",
        "w6 w7 w8 w9 w10",
        "w9 w10 w11",
    ]


def test_chunk_text_empty() -> None:
    assert chunk_text("   ") == []
