from pathlib import Path

SUPPORTED_SUFFIXES = {".md", ".txt"}

DEFAULT_STATE_VERSION = 1

# Safety limits (so your report doesn't become a novel)
MAX_PREVIEW_CHARS = 220
MAX_RAG_SNIPPET_CHARS = 260

def to_posix_relpath(path: Path, base: Path) -> str:
    return path.resolve().relative_to(base.resolve()).as_posix()