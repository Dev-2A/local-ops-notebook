from dataclasses import dataclass
from pathlib import Path
from typing import List

from .constants import SUPPORTED_SUFFIXES, to_posix_relpath
from .hashing import sha256_file
from .state import FileState, StateStore, _now_iso_local


@dataclass
class ScanItem:
    relpath: str
    abspath: Path | None
    status: str     # "unchanged" | "changed" | "new" | "deleted"
    sha256: str | None
    size: int | None
    mtime_epoch: float | None
    last_changed_at: str | None


def iter_note_files(notes_dir: Path) -> List[Path]:
    if not notes_dir.exists():
        return []
    files: List[Path] = []
    for p in notes_dir.rglob("*"):
        if p.is_file() and p.suffix.lower() in SUPPORTED_SUFFIXES:
            files.append(p)
    return sorted(files)


def scan(notes_dir: Path, store: StateStore) -> List[ScanItem]:
    """
    Compare current fingerprints with stored fingerprints.
    Updates store entries (but does NOT save to disk; caller saves).
    """
    now = _now_iso_local()
    
    existing_files = iter_note_files(notes_dir)
    seen: set[str] = set()
    
    results: List[ScanItem] = []
    
    for f in existing_files:
        rel = to_posix_relpath(f, notes_dir)
        seen.add(rel)
        
        sha = sha256_file(f)
        st = f.stat()
        size = int(st.st_size)
        mtime_epoch = float(st.st_mtime)
        
        prev = store.get(rel)
        
        if prev is None:
            status = "new"
            last_changed_at = now
        else:
            if prev.sha256 == sha:
                status = "unchanged"
                last_changed_at = prev.last_changed_at
            else:
                status = "changed"
                last_changed_at = now
        
        # update state
        store.set(
            rel,
            FileState(
                sha256=sha,
                size=size,
                mtime_epoch=mtime_epoch,
                last_changed_at=last_changed_at,
                last_scanned_at=now,
            ),
        )
        
        results.append(
            ScanItem(
                relpath=rel,
                abspath=f,
                status=status,
                sha256=sha,
                size=size,
                mtime_epoch=mtime_epoch,
                last_changed_at=last_changed_at,
            )
        )
    
    # detect deletions
    for rel in store.all_relpaths():
        if rel not in seen:
            prev = store.get(rel)
            # already deleted state? keep as-is, but don't spam weekly report forever:
            # still mark deleted "changed_at" only when first time we notice deletion
            if prev and prev.sha256 is None:
                # already known deleted
                results.append(
                    ScanItem(
                        relpath=rel,
                        abspath=None,
                        status="deleted",
                        sha256=None,
                        size=None,
                        mtime_epoch=None,
                        last_changed_at=prev.last_changed_at,
                    )
                )
                continue
            
            store.mark_deleted(rel)
            prev2 = store.get(rel)
            results.append(
                ScanItem(
                    relpath=rel,
                    abspath=None,
                    status="deleted",
                    sha256=None,
                    size=None,
                    mtime_epoch=None,
                    last_changed_at=prev2.last_changed_at if prev2 else now,
                )
            )
    
    # stable ordering: changed first, then others
    order = {"changed": 0, "new": 1, "deleted": 2, "unchanged": 3}
    results.sort(key=lambda x: (order.get(x.status, 9), x.relpath))
    return results