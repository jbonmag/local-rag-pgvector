from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    index: int
    content: str
    token_count: int


def estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


def chunk_text(text: str, max_tokens: int = 300, overlap_tokens: int = 50) -> list[TextChunk]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    if overlap_tokens < 0 or overlap_tokens >= max_tokens:
        raise ValueError("overlap_tokens must be >= 0 and smaller than max_tokens")

    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    start = 0
    index = 0
    step = max_tokens - overlap_tokens

    while start < len(words):
        end = min(start + max_tokens, len(words))
        content = " ".join(words[start:end]).strip()
        if content:
            chunks.append(
                TextChunk(index=index, content=content, token_count=estimate_tokens(content))
            )
            index += 1
        if end == len(words):
            break
        start += step

    return chunks
