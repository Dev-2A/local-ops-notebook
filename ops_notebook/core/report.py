from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional
import difflib

from .constants import MAX_PREVIEW_CHARS, MAX_RAG_SNIPPET_CHARS
from .scanner import ScanItem, scan
from .state import StateStore
from .weekly import current_week_window_local, parse_iso_maybe
from .rag_client import RagClient, RagEvidence
from .snapshots import SnapshotStore
from .rag_cache import RagCache


MAX_DIFF_LINES = 160


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


def _format_changed_files_block(items: List[ScanItem]) -> str:
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


def _unified_diff_text(old_text: str, new_text: str, relpath: str) -> str:
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    diff_iter = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"a/{relpath}",
        tofile=f"b/{relpath}",
        lineterm="",
    )
    diff_lines = list(diff_iter)
    if not diff_lines:
        return "(no diff)"
    
    if len(diff_lines) > MAX_DIFF_LINES:
        diff_lines = diff_lines[:MAX_DIFF_LINES] + ["...(diff truncated)"]
    return "\n".join(diff_lines)


def _format_diff_block(items: List[ScanItem], notes_dir: Path, snapshots: SnapshotStore) -> str:
    if not items:
        return "- (none)\n"
    
    lines: List[str] = []
    for it in items:
        lines.append(f"### `{it.relpath}` ({it.status})")
        
        if it.status == "deleted" or it.abspath is None:
            lines.append("")
            lines.append("> deleted")
            lines.append("")
            continue
        
        new_text = _read_text_safe(it.abspath)
        old_text = snapshots.load_text(it.relpath) or ""
        
        diff_text = _unified_diff_text(old_text, new_text, it.relpath)
        
        lines.append("")
        lines.append("```diff")
        lines.append(diff_text)
        lines.append("```")
        lines.append("")
    
    return "\n".join(lines).rstrip() + "\n"


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


def _format_rag_block(evidences: Optional[List[RagEvidence]], top_k: int) -> str:
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


def _auto_report_path(reports_dir: Path, week_start: datetime) -> Path:
    iso = week_start.isocalendar() # (year, week, weekday)
    y = iso.year
    w = iso.week
    return reports_dir / f"{y}-W{w:02d}.md"


def generate_weekly_report(
    notes_dir: Path,
    reports_dir: Path,
    report_path: Optional[Path],
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
        print(f"[INFO] reports_dir={reports_dir}")
        print(f"[INFO] state_path={state_path}")
        print(f"[INFO] use_rag={use_rag} rag_url={rag_url} top_k={rag_top_k}")
    
    store = StateStore(state_path)
    store.load()
    
    items = scan(notes_dir, store)
    store.save()
    
    # filter: changed/new/deleted that happened within current week window
    week = current_week_window_local()
    week_range = f"{week.start.date().isoformat()} ~ {(week.end.date()).isoformat()} (Mon~Mon)"
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")
    
    this_week_candidates: List[ScanItem] = []
    for it in items:
        if it.status not in ("changed", "new", "deleted"):
            continue
        dt = parse_iso_maybe(it.last_changed_at)
        if dt is None:
            continue
        if week.start <= dt < week.end:
            this_week_candidates.append(it)
    
    # Output path
    reports_dir.mkdir(parents=True, exist_ok=True)
    final_report_path = report_path if report_path is not None else _auto_report_path(reports_dir, week.start)
    
    # Snapshots (for diffs)
    snapshots_root = state_path.parent / "snapshots"
    snapshots = SnapshotStore(snapshots_root)
    
    # Build blocks
    changed_files_block = _format_changed_files_block(this_week_candidates)
    diff_block = _format_diff_block(this_week_candidates, notes_dir, snapshots)
    auto_digest_block = _format_auto_digest_block(this_week_candidates, notes_dir)
    
    rag_per_file_block = "- (RAG disabled)\n"
    if use_rag:
        client = RagClient(rag_url=rag_url, timeout_s=12)
        
        cache_path = state_path.parent / "rag_cache.json"
        rag_cache = RagCache(cache_path)
        rag_cache.load()
        
        lines: List[str] = []
        for it in this_week_candidates:
            if it.status == "deleted" or it.abspath is None:
                lines.append(f"### `{it.relpath}`")
                lines.append("- (deleted)\n")
                continue
            
            # query 구성: 제목 + 파일명 + preview
            text = _read_text_safe(it.abspath)
            title = _first_heading_or_filename(text, Path(it.relpath).name)
            pv = _preview(text, limit=180)
            q = f"{title}\n파일: {it.relpath}\n내용요약: {pv}\n관련 근거/관련 노트를 찾아줘"
            
            # 캐시 키: relpath + sha256 + url + topk + max_chars
            sha = it.sha256 or ""
            cached = rag_cache.get(it.relpath, sha, rag_url, rag_top_k, MAX_RAG_SNIPPET_CHARS)
            
            lines.append(f"### `{it.relpath}`")
            if cached is not None:
                evs = cached
            else:
                try:
                    evs = client.query_topk(query=q, top_k=rag_top_k, max_chars=MAX_RAG_SNIPPET_CHARS)
                except Exception:
                    evs = []
                rag_cache.set(it.relpath, sha, rag_url, rag_top_k, MAX_RAG_SNIPPET_CHARS, evs)
            
            if not evs:
                lines.append("- (no evidence)\n")
                continue
            
            for i, ev in enumerate(evs, start=1):
                snippet = (ev.snippet or "").strip().replace("\n", " ")
                if len(snippet) > MAX_RAG_SNIPPET_CHARS:
                    snippet = snippet[:MAX_RAG_SNIPPET_CHARS].rstrip() + "..."
                src = f" — source: {ev.source}" if ev.source else ""
                score = f"  (score={ev.score:.4f})" if ev.score is not None else ""
                lines.append(f"- Top{i}{score}{src}")
            lines.append("")
        
        rag_cache.save()
        rag_per_file_block = "\n".join(lines).rstrip() + "\n"
    
    template = template_path.read_text(encoding="utf-8")
    out = template.format(
        week_range=week_range,
        generated_at=generated_at,
        report_file=final_report_path.as_posix(),
        changed_files_block=changed_files_block,
        diff_block=diff_block,
        auto_digest_block=auto_digest_block,
        rag_top_k=rag_top_k,
        rag_per_file_block=rag_per_file_block,
    )
    
    final_report_path.parent.mkdir(parents=True, exist_ok=True)
    final_report_path.write_text(out, encoding="utf-8")
    
    # Update snapshots AFTER report generation (so diff uses previous snapshot)
    for it in items:
        if it.abspath is None or it.status == "deleted":
            snapshots.delete(it.relpath)
            continue
        try:
            snapshots.save_text(it.relpath, _read_text_safe(it.abspath))
        except Exception:
            # best effort
            pass
    
    if verbose:
        print(f"[DONE] wrote: {report_path}")
    else:
        print(f"[OK] weekly report generated: {report_path}")