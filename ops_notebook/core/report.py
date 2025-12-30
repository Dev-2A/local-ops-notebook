from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from .constants import MAX_PREVIEW_CHARS, MAX_RAG_SNIPPET_CHARS
from .scanner import ScanItem, scan
from .state import StateStore
from .weekly import current_week_window_local, parse_iso_maybe
from .rag_client import RagClient, RagEvidence


def _read_text_safe(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        # fallback
        return path.read_text(encoding="utf-8", errors="replace")


def _first_heading_or_filename(text: str, fallback_name: str) -> str:
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#"):
            return line.lstrip("#").strip() or fallback_name
    return fallback_name


def _preview(text: str, limit: int = MAX_PREVIEW_CHARS) -> str:
    t = " ".join(text.split())
    if len(t) <= limit:
        return t
    return t[:limit].rstrip() + "..."


def _format_changed_files_block(items: List[ScanItem], only_this_week: bool = True) -> str:
    if not items:
        return "- (none)\n"
    lines = []
    for it in items:
        badge = {
            "changed": "🟧 changed",
            "new": "🟩 new",
            "deleted": "🟥 deleted",
            "unchanged": "⬜ unchanged",
        }.get(it.status, it.status)
        lines.append(f"- {badge}: `{it.relpath}`")
    return "\n".join(lines) + "\n"


def _format_auto_digest_block(items: List[ScanItem], notes_dir: Path) -> str:
    if not items:
        return "- (none)\n"
    
    lines: List[str] = []
    for it in items:
        if it.status == "deleted" or it.abspath is None:
            lines.append(f"- `{it.relpath}`: (deleted)")
            continue
        
        text = _read_text_safe(it.abspath)
        title = _first_heading_or_filename(text, Path(it.relpath).name)
        prev = _preview(text)
        lines.append(f"- `{it.relpath}` — **{title}**")
        lines.append(f"  - preview: {prev}")
    return "\n".join(lines) + "\n"


def _default_rag_query(changed_items: List[ScanItem], notes_dir: Path) -> str:
    """
    Construct a reasonable query without being fancy:
    - Prefer titles (first # heading), else filename
    """
    titles: List[str] = []
    for it in changed_items[:15]:
        if it.status == "deleted" or it.abspath is None:
            titles.append(Path(it.relpath).stem)
            continue
        text = _read_text_safe(it.abspath)
        titles.append(_first_heading_or_filename(text, Path(it.relpath).stem))
    
    if not titles:
        return "이번 주 변경된 노트 근거를 찾아줘"
    
    joined = ", ".join(titles[:15])
    return f"이번 주 변경된 노트({joined})와 관련된 근거/관련 노트를 찾아줘"


def _format_rag_block(evidences: List[RagEvidence] | None, top_k: int) -> str:
    if not evidences:
        return "- (RAG disabled or no evidence)\n"
    
    lines: List[str] = []
    for i, ev in enumerate(evidences[:top_k], start=1):
        snippet = ev.snippet.strip().replace("\n", " ")
        if len(snippet) > MAX_RAG_SNIPPET_CHARS:
            snippet = snippet[:MAX_RAG_SNIPPET_CHARS].rstrip() + "..."
        
        src = f" — source: {ev.source}" if ev.source else ""
        score = f" (score={ev.score:.4f})" if ev.score is not None else ""
        lines.append(f"- Top{i}{score}{src}")
        lines.append(f"  - {snippet}")
    return "\n".join(lines) + "\n"


def generate_weekly_report(
    notes_dir: Path,
    report_path: Path,
    template_path: Path,
    state_path: Path,
    use_rag: bool,
    rag_url: str,
    rag_top_k: int,
    rag_query: str,
    verbose: bool = False,
) -> None:
    if verbose:
        print(f"[INFO] notes_dir={notes_dir}")
        print(f"[INFO] report_path={report_path}")
        print(f"[INFO] state_path={state_path}")
        print(f"[INFO] use_rag={use_rag} rag_url={rag_url} top_k={rag_top_k}")
    
    store = StateStore(state_path)
    store.load()
    
    items = scan(notes_dir, store)
    store.save()
    
    # filter: changed/new/deleted that happened within current week window
    week = current_week_window_local()
    this_week_candidates: List[ScanItem] = []
    for it in items:
        if it.status not in ("changed", "new", "deleted"):
            continue
        dt = parse_iso_maybe(it.last_changed_at)
        if dt is None:
            continue
        if week.start <= dt < week.end:
            this_week_candidates.append(it)
    
    week_range = f"{week.start.date().isoformat()} ~ {(week.end.date()).isoformat()} (Mon~Mon)"
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    
    changed_files_block = _format_changed_files_block(this_week_candidates)
    auto_digest_block = _format_auto_digest_block(this_week_candidates, notes_dir)
    
    evidences = None
    if use_rag:
        client = RagClient(rag_url=rag_url, timeout_s=12)
        query = rag_query if rag_query else _default_rag_query(this_week_candidates, notes_dir)
        if verbose:
            print(f"[INFO] RAG query: {query}")
        try:
            evidences = client.query_topk(query=query, top_k=rag_top_k)
        except Exception as e:
            # don't fail the whole report
            evidences = []
            if verbose:
                print(f"[WARN] RAG failed: {e}")
    
    rag_block = _format_rag_block(evidences, rag_top_k)
    
    template = template_path.read_text(encoding="utf-8")
    out = template.format(
        week_range=week_range,
        generated_at=generated_at,
        changed_files_block=changed_files_block,
        auto_digest_block=auto_digest_block,
        rag_top_k=rag_top_k,
        rag_evidence_block=rag_block,
    )
    
    report_path.write_text(out, encoding="utf-8")
    
    if verbose:
        print(f"[DONE] wrote: {report_path}")
    else:
        print(f"[OK] weekly report generated: {report_path}")