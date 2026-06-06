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
