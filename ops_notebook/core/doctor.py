from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .rag_client import RagClient


@dataclass
class DoctorResult:
    ok: bool
    summary: str
    details: str


def _exists_file(p: Path) -> bool:
    return p.exists() and p.is_file()


def _exists_dir(p: Path) -> bool:
    return p.exists() and p.is_dir()


def _writable_dir(p: Path) -> bool:
    try:
        p.mkdir(parents=True, exist_ok=True)
        probe = p / ".write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return True
    except Exception:
        return False


def run_doctor(
    notes_dir: Path,
    reports_dir: Path,
    template_path: Path,
    state_path: Path,
    use_rag: bool,
    rag_url: str,
) -> DoctorResult:
    lines = []
    ok = True
    
    #notes dir
    if _exists_dir(notes_dir):
        lines.append(f"[OK] notes_dir exists: {notes_dir}")
    else:
        ok = False
        lines.append(f"[FAIL] notes_dir missing: {notes_dir}")
    
    # template
    if _exists_file(template_path):
        lines.append(f"[OK] template exists: {template_path}")
    else:
        ok = False
        lines.append(f"[FAIL] template missing: {template_path}")
    
    # reports writable
    if _writable_dir(reports_dir):
        lines.append(f"[OK] reports_dir writable: {reports_dir}")
    else:
        ok = False
        lines.append(f"[FAIL] reports_dir not writable: {reports_dir}")
    
    # state writable
    if _writable_dir(state_path.parent):
        lines.append(f"[OK] state_dir writable: {state_path.parent}")
    else:
        ok = False
        lines.append(f"[FAIL] state_dir not writable: {state_path.parent}")
    
    # rag (optional)
    if use_rag:
        try:
            clinet = RagClient(rag_url=rag_url, timeout_s=5)
            evs = clinet.query_topk(query="doctor ping", top_k=1, max_chars=80)
            if evs is not None:
                lines.append(f"[OK] RAG reachable: {rag_url}")
            else:
                ok = False
                lines.append(f"[FAIL] RAG returned no response: {rag_url}")
        except Exception as e:
            ok = False
            lines.append(f"[FAIL] RAG unreachable: {rag_url} ({e})")
    else:
        lines.append("[OK] RAG disabled")
    
    summary = "DOCTOR OK" if ok else "DOCTOR FAIL"
    details = "\n".join(lines)
    return DoctorResult(ok=ok, summary=summary, details=details)