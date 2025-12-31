from __future__ import annotations

from pathlib import Path

# 너무 큰 노트가 있어도 운영룰이 죽지 않도록 안전장치
MAX_SNAPSHOT_CHARS = 200_000


class SnapshotStore:
    """
    Stores last-known text snapshot per relpath under:
      .ops_state/snapshots/<relpath>
    
    This allows generating diffs between previous and current runs.
    """
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
    
    def _path_for(self, relpath: str) -> Path:
        # relpath is POSIX-like (scanner produces /). Path() will handle it on Windows too.
        p = self.root_dir / Path(relpath)
        return p
    
    def load_text(self, relpath: str) -> str | None:
        p = self._path_for(relpath)
        if not p.exists():
            return None
        try:
            return p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return None
    
    def save_text(self, relpath: str, text: str) -> None:
        p = self._path_for(relpath)
        p.parent.mkdir(parents=True, exist_ok=True)
        
        if len(text) > MAX_SNAPSHOT_CHARS:
            text = text[:MAX_SNAPSHOT_CHARS] + "\n\n... (snapshot truncated)\n"
        
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(p)
    
    def delete(self, relpath: str) -> None:
        p = self._path_for(relpath)
        try:
            if p.exists():
                p.unlink()
        except Exception:
            # best effort
            pass