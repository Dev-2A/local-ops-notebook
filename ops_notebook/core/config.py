from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


DEFAULT_CONFIG: Dict[str, Any] = {
    "notes_dir": "notes",
    "reports_dir": "reports",
    "template_path": "templates/weekly_report_template.md",
    "state_path": ".ops_state/fingerprints.json",
    # optional: explicit output path, otherwise auto (reports/YYYY-Www.md)
    "report_path": "",
    "rag": {
        "enabled": False,
        "url": "http://127.0.0.1:8000/query",
        "top_k": 3,
        "query": "",
    },
}


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: Path) -> Dict[str, Any]:
    """
    Loads YAML config and merges it on top of DEFAULT_CONFIG.
    If file doesn't exist, returns DEFAULT_CONFIG.
    """
    if not path.exists():
        return dict(DEFAULT_CONFIG)
    
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception:
        # fail-safe: don't break ops
        return dict(DEFAULT_CONFIG)
    
    if not isinstance(raw, dict):
        return dict(DEFAULT_CONFIG)
    
    merged = _deep_merge(DEFAULT_CONFIG, raw)
    # basic normalization
    if "rag" not in merged or not isinstance(merged["rag"], dict):
        merged["rag"] = dict(DEFAULT_CONFIG["rag"])
    return merged