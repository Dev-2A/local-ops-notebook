from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass(frozen=True)
class RagEvidence:
    snippet: str
    source: Optional[str] = None
    score: Optional[float] = None


class RagClient:
    """
    Tries to be tolerant to unknown response formats.
    Expected server: local-rag-kit like endpoint at /query
    
    We'll try:
        POST { "query": "...", "top_k": 3 }
        POST { "query": "...", "k": 3 }
        GET  ?query=...&top_k=...
    """
    
    def __init__(self, rag_url: str, timeout_s: int = 10):
        self.rag_url = rag_url
        self.timeout_s = timeout_s
    
    def query_topk(self, query: str, top_k: int = 3) -> List[RagEvidence]:
        # 1) POST top_k
        payloads = [
            {"query": query, "top_k": top_k},
            {"query": query, "k": top_k},
        ]
        
        last_err: Exception | None = None
        for pl in payloads:
            try:
                r = requests.post(self.rag_url, json=pl, timeout=self.timeout_s)
                if r.status_code >= 400:
                    continue
                return self._parse_any(r.json(), top_k=top_k)
            except Exception as e:
                last_err = e
        
        # 2) GET fallback
        try:
            r = requests.get(self.rag_url, params={"query": query, "top_k": top_k}, timeout=self.timeout_s)
            if r.status_code < 400:
                return self._parse_any(r.json(), top_k=top_k)
        except Exception as e:
            last_err = e
        
        if last_err:
            raise last_err
        return []
    
    def _parse_any(self, data: Any, top_k: int) -> List[RagEvidence]:
        """
        Accept common shapes:
        - {"contexts":[{"text":..., "source":..., "score":...}, ...]}
        - {"sources":[{"content"/"text":..., ...}, ...]}
        - {"documents":[...]}
        - {"topk":[...]}
        - {"results":[...]}
        - list[...] directly
        """
        candidates = None
        
        if isinstance(data, list):
            candidates = data
        elif isinstance(data, dict):
            for key in ("contexts", "sources", "documents", "topk", "results", "hits"):
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
            source = item.get("source") or item.get("file") or item.get("doc_id") or item.get("title")
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