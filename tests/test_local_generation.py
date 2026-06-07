import pytest

from app.config import Settings
from app.llm.local_generation import LocalGenerator


def test_mock_generation_backend_always_works() -> None:
    generator = LocalGenerator(Settings(local_llm_backend="mock"))
    answer = generator.generate("Question", [{"content": "retrieved content"}])
    assert "retrieved content" in answer


def test_llama_cpp_missing_model_has_clear_error() -> None:
    settings = Settings(local_llm_backend="llama_cpp", local_llm_model_path="./missing/model.gguf")
    with pytest.raises(RuntimeError, match="GGUF"):
        LocalGenerator(settings)


def test_transformers_missing_model_has_clear_error() -> None:
    settings = Settings(
        local_llm_backend="transformers", local_llm_model_path="./missing/model-folder"
    )
    with pytest.raises(RuntimeError, match="local model folder"):
        LocalGenerator(settings)
