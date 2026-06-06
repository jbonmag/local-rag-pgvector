import hashlib
import math
from collections.abc import Sequence
from pathlib import Path

from app.config import Settings, get_settings


class LocalEmbeddings:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.backend = self.settings.embeddings_backend.lower()
        self.dimension = self.settings.embedding_dimension
        self.model_name = self._model_name()
        self._model = None

        if self.backend not in {"mock", "sentence_transformers"}:
            raise ValueError(f"Unsupported embeddings backend: {self.backend}")
        if self.backend == "sentence_transformers":
            self._model = self._load_sentence_transformer()

    def embed_texts(self, texts: Sequence[str]) -> list[list[float]]:
        if self.backend == "mock":
            return [mock_embedding(text, self.dimension) for text in texts]

        embeddings = self._model.encode(
            list(texts), normalize_embeddings=True, batch_size=32, show_progress_bar=False
        )
        return [list(map(float, embedding)) for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        return self.embed_texts([text])[0]

    def _model_name(self) -> str:
        if self.backend == "mock":
            return f"mock-{self.dimension}"
        model_path = self.settings.embedding_model_path
        return str(model_path) if model_path.exists() else self.settings.embedding_model_name

    def _load_sentence_transformer(self):
        model_path = Path(self.settings.embedding_model_path)
        if model_path.exists():
            source = str(model_path)
        elif self.settings.allow_model_download:
            source = self.settings.embedding_model_name
        else:
            raise RuntimeError(
                "Embedding model path does not exist and ALLOW_MODEL_DOWNLOAD=false: "
                f"{model_path}. Download it first with scripts/download_model.py or use "
                "EMBEDDINGS_BACKEND=mock."
            )

        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is not installed. Run: pip install -e \".[local-llm]\""
            ) from exc

        return SentenceTransformer(
            source,
            token=self.settings.hf_token or None,
            local_files_only=not self.settings.allow_model_download,
        )


def mock_embedding(text: str, dimension: int) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimension:
        digest = hashlib.sha256(f"{counter}:{text}".encode()).digest()
        for byte in digest:
            values.append((byte / 127.5) - 1.0)
            if len(values) == dimension:
                break
        counter += 1

    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]
