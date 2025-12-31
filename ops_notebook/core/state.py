import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .constants import DEFAULT_STATE_VERSION


def _now_iso_local() -> str:
    # local timezone offset aware timestamp (Windows-friendly)
    return datetime.now().astimezone().isoformat(timespec="seconds")


@dataclass
class FileState:
    sha256: Optional[str]
    size: Optional[int]
    mtime_epoch: Optional[float]
    last_changed_at: Optional[str]
    last_scanned_at: Optional[str]
    status: Optional[str] = None # runtime only (not required in persisted)


class StateStore:
    def __init__(self, state_path: Path):
        self.state_path = state_path
        self.data: Dict[str, Any] = {
            "version": DEFAULT_STATE_VERSION,
            "files": {},    # relpath -> file state dict
            "last_run_at": None,
        }
    
    def load(self) -> None:
        if not self.state_path.exists():
            return
        try:
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict) and "files" in raw:
                self.data = raw
        except Exception:
            # if corrupted, don't crash ops. start fresh.
            self.data = {
                "version": DEFAULT_STATE_VERSION,
                "files": {},
                "last_run_at": None,
            }
    
    def save(self) -> None:
        self.data["last_run_at"] = _now_iso_local()
        tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.state_path)
    
    def get(self, relpath: str) -> Optional[FileState]:
        fs = self.data.get("files", {}).get(relpath)
        if not isinstance(fs, dict):
            return None
        return FileState(
            sha256=fs.get("sha256"),
            size=fs.get("size"),
            mtime_epoch=fs.get("mtime_epoch"),
            last_changed_at=fs.get("last_changed_at"),
            last_scanned_at=fs.get("last_scanned_at"),
        )
    
    def set(self, relpath: str, fs: FileState) -> None:
        self.data.setdefault("files", {})[relpath] = {
            "sha256": fs.sha256,
            "size": fs.size,
            "mtime_epoch": fs.mtime_epoch,
            "last_changed_at": fs.last_changed_at,
            "last_scanned_at": fs.last_scanned_at,
        }
    
    def mark_deleted(self, relpath: str) -> None:
        prev = self.get(relpath)
        now = _now_iso_local()
        if prev is None:
            prev = FileState(None, None, None, None, None)
        
        prev.sha256 = None
        prev.size = None
        prev.mtime_epoch = None
        prev.last_scanned_at = now
        prev.last_changed_at = now
        self.set(relpath, prev)
    
    def all_relpaths(self) -> list[str]:
        files = self.data.get("files", {})
        if not isinstance(files, dict):
            return []
        return list(files.keys())