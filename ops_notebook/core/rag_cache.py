from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from .rag_client import RagEvidence


class RagCache:
    def __init__(self, path: Path):
        self.path = path
        self.data: Dict[str, Any] = {"version": 1, "items": {}}

    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict) and isinstance(loaded.get("items"), dict):
                self.data = loaded
            else:
                self.data = {"version": 1, "items": {}}
        except Exception:
            self.data = {"version": 1, "items": {}}

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(json.dumps(self.data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def get(
        self,
        relpath: str,
        sha256: str,
        rag_url: str,
        top_k: int,
        max_chars: int,
    ) -> Optional[List[RagEvidence]]:
        item = self.data.get("items", {}).get(relpath)
        if not isinstance(item, dict):
            return None

        if item.get("sha256") != sha256:
            return None
        if item.get("rag_url") != rag_url:
            return None
        if int(item.get("top_k", -1)) != int(top_k):
            return None
        if int(item.get("max_chars", -1)) != int(max_chars):
            return None

        evs: List[RagEvidence] = []
        for ev in item.get("evidences", []) or []:
            if not isinstance(ev, dict):
                continue
            evs.append(
                RagEvidence(
                    snippet=str(ev.get("snippet", "")),
                    source=ev.get("source"),
                    score=ev.get("score"),
                )
            )
        return evs

    def set(
        self,
        relpath: str,
        sha256: str,
        rag_url: str,
        top_k: int,
        max_chars: int,
        evidences: List[RagEvidence],
    ) -> None:
        self.data.setdefault("items", {})[relpath] = {
            "sha256": sha256,
            "rag_url": rag_url,
            "top_k": int(top_k),
            "max_chars": int(max_chars),
            "evidences": [
                {"snippet": e.snippet, "source": e.source, "score": e.score} for e in evidences
            ],
        }
