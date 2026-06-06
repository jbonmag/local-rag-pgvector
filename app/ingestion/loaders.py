from dataclasses import dataclass
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

SUPPORTED_SUFFIXES = {".txt", ".md", ".markdown", ".html", ".htm", ".pdf"}


@dataclass(frozen=True)
class LoadedDocument:
    path: Path
    source_type: str
    title: str
    text: str
    metadata: dict


def iter_supported_files(raw_dir: Path) -> list[Path]:
    if not raw_dir.exists():
        return []
    return sorted(
        path
        for path in raw_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def load_file(path: Path, base_dir: Path | None = None) -> LoadedDocument:
    suffix = path.suffix.lower()
    if suffix in {".txt", ".md", ".markdown"}:
        text = path.read_text(encoding="utf-8", errors="replace")
        source_type = "markdown" if suffix in {".md", ".markdown"} else "txt"
    elif suffix in {".html", ".htm"}:
        html = path.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        title_node = soup.find("title")
        text = soup.get_text(" ", strip=True)
        source_type = "html"
        title = title_node.get_text(strip=True) if title_node else path.stem
        return LoadedDocument(path, source_type, title, text, _metadata(path, base_dir))
    elif suffix == ".pdf":
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        source_type = "pdf"
    else:
        raise ValueError(f"Unsupported file type: {suffix}")

    return LoadedDocument(path, source_type, path.stem, text, _metadata(path, base_dir))


def source_uri_for(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir)).replace("\\", "/")
    except ValueError:
        return str(path.resolve())


def _metadata(path: Path, base_dir: Path | None) -> dict:
    stat = path.stat()
    metadata = {
        "filename": path.name,
        "extension": path.suffix.lower(),
        "size_bytes": stat.st_size,
    }
    if base_dir is not None:
        metadata["source_uri"] = source_uri_for(path, base_dir)
    return metadata
