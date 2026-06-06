from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://rag:rag@localhost:5432/ragdb"
    rag_default_tenant_id: str = "local"

    local_llm_backend: str = "mock"
    local_llm_model_path: Path = Path("./models/llm/model.gguf")
    local_llm_context_size: int = 4096
    local_llm_max_tokens: int = 512
    local_llm_temperature: float = 0.2
    local_llm_n_gpu_layers: int = 0
    local_llm_device: str = "auto"
    local_llm_dtype: str = "auto"

    embeddings_backend: str = "mock"
    embedding_model_path: Path = Path("./models/embeddings/model")
    embedding_model_name: str = "intfloat/multilingual-e5-small"
    embedding_dimension: int = Field(default=384, ge=1)

    allow_model_download: bool = False
    hf_token: str | None = None

    data_raw_dir: Path = Path("./data/raw")
    data_processed_dir: Path = Path("./data/processed")
    rag_min_vector_score: float = 0.75


@lru_cache
def get_settings() -> Settings:
    return Settings()
