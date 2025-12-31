from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

import requests


@dataclass(frozen=True)
class RagEvidence:
    snippet: str
    source: Optional[str] = None    # doc / file path
    score: Optional[float] = None


class RagClient:
    """
    Compatible with local-rag-kit api_hybrid.py:
      POST /query
        { query, top_k, include_text, max_chars, ... }
      Response:
        { ..., chunks: [ {rank, score, doc, chunk_index, ..., text?}, ... ] }
    """
    
    def __init__(self, rag_url: str, timeout_s: int = 12):
        self.rag_url = rag_url
        self.timeout_s = timeout_s
    
    def query_topk(self, query: str, top_k: int = 3, max_chars: int = 260) -> List[RagEvidence]:
        # 1) POST top_k
        payload = {
            "query": query,
            "top_k": int(top_k),
            # IMPORTANT: api_hybrid default include_text=False -> must request text
            "include_text": True,
            "max_chars": int(max_chars),
            # keep defaults: mode="hybrid", etc.
        }
        
        r = requests.post(self.rag_url, json=payload, timeout=self.timeout_s)
        r.raise_for_status()
        return self._parse_any(r.json(), top_k=top_k)
    
    def _parse_any(self, data: Any, top_k: int) -> List[RagEvidence]:
        """
        Accept shapes:
        - local-rag-kit: {"chunks":[...]}  (primary)
        - {"contexts"/"sources"/"documents"/"results"/"topk":[...]}
        - ES-like hits
        - list[...] directly
        """
        candidates = None
        
        if isinstance(data, list):
            candidates = data
        elif isinstance(data, dict):
            for key in ("chunks", "contexts", "sources", "documents", "topk", "results", "hits"):
                v = data.get(key)
                if isinstance(v, list):
                    candidates = v
                    break
            if candidates is None:
                # maybe ES-like: {"hits":{"hits":[{"_source":...},...]}}
                hits = data.get("hits")
                if isinstance(hits, dict) and isinstance(hits.get("hits"), list):
                    candidates = hits["hits"]
        
        if not isinstance(candidates, list):
            return []
        
        evs: List[RagEvidence] = []
        for item in candidates:
            ev = self._parse_item(item)
            if ev and ev.snippet.strip():
                evs.append(ev)
            if len(evs) >= top_k:
                break
        return evs
    
    def _parse_item(self, item: Any) -> RagEvidence | None:
        if item is None:
            return None
        
        # ES hit style
        if isinstance(item, dict) and "_source" in item and isinstance(item["_source"], dict):
            src = item["_source"]
            return RagEvidence(
                snippet=str(src.get("text") or src.get("content") or src.get("chunk") or src.get("body") or ""),
                source=str(src.get("source") or src.get("file") or src.get("doc_id") or ""),
                score=self._maybe_float(item.get("_score")),
            )

        if isinstance(item, dict):
            snippet = item.get("text") or item.get("content") or item.get("chunk") or item.get("body") or item.get("snippet")
            source = item.get("doc") or item.get("source") or item.get("file") or item.get("doc_id") or item.get("title")
            score = item.get("score") or item.get("_score") or item.get("similarity")
            return RagEvidence(
                snippet=str(snippet or ""),
                source=str(source) if source is not None else None,
                score=self._maybe_float(score),
            )

        # fallback: stringify
        return RagEvidence(snippet=str(item))

    def _maybe_float(self, v: Any) -> float | None:
        try:
            if v is None:
                return None
            return float(v)
        except Exception:
            return None