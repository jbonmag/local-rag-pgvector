from pathlib import Path
from typing import Any

from app.config import Settings, get_settings
from app.llm.prompts import DEFAULT_SYSTEM_PROMPT


class LocalGenerator:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.backend = self.settings.local_llm_backend.lower()
        self._generator: Any = None

        if self.backend == "mock":
            self._generator = MockGenerator()
        elif self.backend == "llama_cpp":
            self._generator = LlamaCppGenerator(self.settings)
        elif self.backend == "transformers":
            self._generator = TransformersGenerator(self.settings)
        else:
            raise ValueError(f"Unsupported LOCAL_LLM_BACKEND: {self.backend}")

    def generate(
        self, question: str, contexts: list[dict], system_prompt: str | None = None
    ) -> str:
        return self._generator.generate(question, contexts, system_prompt or DEFAULT_SYSTEM_PROMPT)


class MockGenerator:
    def generate(
        self, question: str, contexts: list[dict], system_prompt: str | None = None
    ) -> str:
        if not contexts:
            return "There is not enough information in the local documents to answer."
        snippets = " ".join(context.get("content", "") for context in contexts[:2]).strip()
        if not snippets:
            return "There is not enough information in the local documents to answer."
        return f"According to the local documents, {snippets[:700]}"


class LlamaCppGenerator:
    def __init__(self, settings: Settings):
        model_path = Path(settings.local_llm_model_path)
        if not model_path.is_file():
            raise RuntimeError(
                "LOCAL_LLM_BACKEND=llama_cpp requires a GGUF file at LOCAL_LLM_MODEL_PATH. "
                f"Missing file: {model_path}"
            )
        try:
            from llama_cpp import Llama
        except ImportError as exc:
            raise RuntimeError(
                "llama-cpp-python is not installed. Run: pip install -e \".[local-llm]\""
            ) from exc

        self.settings = settings
        self.model = Llama(
            model_path=str(model_path),
            n_ctx=settings.local_llm_context_size,
            n_gpu_layers=settings.local_llm_n_gpu_layers,
            verbose=False,
        )

    def generate(
        self, question: str, contexts: list[dict], system_prompt: str | None = None
    ) -> str:
        prompt = build_context_prompt(question, contexts, system_prompt or DEFAULT_SYSTEM_PROMPT)
        result = self.model(
            prompt,
            max_tokens=self.settings.local_llm_max_tokens,
            temperature=self.settings.local_llm_temperature,
            stop=["</s>"],
        )
        return result["choices"][0]["text"].strip()


class TransformersGenerator:
    def __init__(self, settings: Settings):
        model_path = Path(settings.local_llm_model_path)
        if not model_path.is_dir():
            raise RuntimeError(
                "LOCAL_LLM_BACKEND=transformers requires a local model folder at "
                f"LOCAL_LLM_MODEL_PATH. Missing folder: {model_path}"
            )
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer
        except ImportError as exc:
            raise RuntimeError(
                "transformers, torch, and accelerate are not installed. "
                "Run: pip install -e \".[local-llm]\""
            ) from exc

        dtype = (
            "auto"
            if settings.local_llm_dtype == "auto"
            else getattr(torch, settings.local_llm_dtype)
        )
        device_map = settings.local_llm_device
        if device_map == "auto":
            device_map = "auto"

        self.settings = settings
        self.tokenizer = AutoTokenizer.from_pretrained(str(model_path), local_files_only=True)
        self.model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            torch_dtype=dtype,
            device_map=device_map,
        )

    def generate(
        self, question: str, contexts: list[dict], system_prompt: str | None = None
    ) -> str:
        prompt = build_context_prompt(question, contexts, system_prompt or DEFAULT_SYSTEM_PROMPT)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=self.settings.local_llm_max_tokens,
            temperature=self.settings.local_llm_temperature,
            do_sample=self.settings.local_llm_temperature > 0,
            pad_token_id=self.tokenizer.eos_token_id,
        )
        decoded = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return decoded[len(prompt) :].strip() if decoded.startswith(prompt) else decoded.strip()


def build_context_prompt(question: str, contexts: list[dict], system_prompt: str) -> str:
    context_text = "\n\n".join(
        f"[{idx + 1}] {context.get('title') or 'Untitled'}\n{context.get('content', '')}"
        for idx, context in enumerate(contexts)
    )
    return (
        f"{system_prompt}\n\n"
        f"Context:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer in the same language as the question. Cite only the supplied context."
    )
