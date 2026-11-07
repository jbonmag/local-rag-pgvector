from app.config import Settings
from app.llm.local_embeddings import LocalEmbeddings


def test_mock_embeddings_are_deterministic() -> None:
    settings = Settings(embeddings_backend="mock", embedding_dimension=8)
    client = LocalEmbeddings(settings)
    assert client.embed_query("same") == client.embed_query("same")
    assert len(client.embed_query("same")) == 8


def test_mock_embeddings_need_no_real_model() -> None:
    settings = Settings(
        embeddings_backend="mock",
        embedding_model_path="./models/embeddings/does-not-exist",
        embedding_dimension=4,
    )
    assert len(LocalEmbeddings(settings).embed_query("x")) == 4


def test_e5_models_get_query_and_passage_prefixes() -> None:
    from app.llm.local_embeddings import add_e5_prefix

    model = "intfloat/multilingual-e5-small"
    assert add_e5_prefix("what is X?", "query", model) == "query: what is X?"
    assert add_e5_prefix("X is a thing.", "passage", model) == "passage: X is a thing."
    assert add_e5_prefix("query: already", "query", model) == "query: already"


def test_other_models_get_text_unchanged() -> None:
    from app.llm.local_embeddings import add_e5_prefix

    assert add_e5_prefix("what is X?", "query", "BAAI/bge-small-en-v1.5") == "what is X?"
