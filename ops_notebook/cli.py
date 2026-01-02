import argparse
import os
from pathlib import Path

from ops_notebook.core.config import load_config
from ops_notebook.core.report import generate_weekly_report


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def _env_int(name: str) -> int | None:
    v = os.getenv(name)
    if v is None:
        return None
    try:
        return int(v.strip())
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ops_notebook",
        description="Local Ops Notebook - fingerprint change detection + weekly report",
    )

    # NEW: config
    parser.add_argument("--config", default="config.yaml", help="Config path (default: config.yaml)")

    # Optional overrides (if omitted, config.yaml (or defaults) are used)
    parser.add_argument("--notes", default=None, help="Notes folder override")
    parser.add_argument("--template", default=None, help="Template path override")
    parser.add_argument("--reports-dir", default=None, help="Reports directory override")
    parser.add_argument("--report", default=None, help="Explicit report path override (optional)")
    parser.add_argument("--state", default=None, help="State json path override")

    # RAG overrides
    parser.add_argument("--use-rag", action="store_true", help="Enable RAG evidence (override config/env)")
    parser.add_argument("--rag-url", default=None, help="RAG server URL override")
    parser.add_argument("--rag-top-k", type=int, default=None, help="RAG top-k override")
    parser.add_argument("--rag-query", default=None, help="Custom query override (optional)")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    parser.add_argument("--doctor", action="store_true", help="Run health check and exit")

    args = parser.parse_args()

    cfg = load_config(Path(args.config))

    notes_dir = Path(args.notes or cfg.get("notes_dir") or "notes")
    template_path = Path(args.template or cfg.get("template_path") or "templates/weekly_report_template.md")
    reports_dir = Path(args.reports_dir or cfg.get("reports_dir") or "reports")

    # report_path: CLI override > config value > None (auto)
    report_arg = args.report
    if report_arg is not None:
        report_path = Path(report_arg) if report_arg.strip() else None
    else:
        cfg_report = str(cfg.get("report_path") or "").strip()
        report_path = Path(cfg_report) if cfg_report else None

    state_path = Path(args.state or cfg.get("state_path") or ".ops_state/fingerprints.json")

    # RAG enable order:
    # 1) CLI --use-rag
    # 2) env USE_RAG
    # 3) config rag.enabled
    rag_cfg = cfg.get("rag") or {}
    use_rag = bool(args.use_rag or _env_bool("USE_RAG", False) or bool(rag_cfg.get("enabled", False)))

    # URL / top_k / query: CLI > env > config > default
    rag_url = args.rag_url or os.getenv("RAG_URL") or rag_cfg.get("url") or "http://127.0.0.1:8000/query"
    rag_top_k = (
        args.rag_top_k
        if args.rag_top_k is not None
        else (_env_int("RAG_TOP_K") or int(rag_cfg.get("top_k") or 3))
    )
    rag_query = (
        args.rag_query
        if args.rag_query is not None
        else (os.getenv("RAG_QUERY") or str(rag_cfg.get("query") or ""))
    ).strip()

    reports_dir.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)

    if args.verbose:
        print(f"[INFO] config={args.config}")
        print(f"[INFO] notes_dir={notes_dir}")
        print(f"[INFO] reports_dir={reports_dir}")
        print(f"[INFO] template_path={template_path}")
        print(f"[INFO] state_path={state_path}")
        print(f"[INFO] report_path={report_path}")
        print(f"[INFO] use_rag={use_rag} rag_url={rag_url} top_k={rag_top_k}")
    
    if args.doctor:
        from ops_notebook.core.doctor import run_doctor
        
        res = run_doctor(
            notes_dir=notes_dir,
            reports_dir=reports_dir,
            template_path=template_path,
            state_path=state_path,
            use_rag=use_rag,
            rag_url=rag_url,
        )
        print(res.summary)
        print(res.details)
        return 0 if res.ok else 2

    generate_weekly_report(
        notes_dir=notes_dir,
        reports_dir=reports_dir,
        report_path=report_path,
        template_path=template_path,
        state_path=state_path,
        use_rag=use_rag,
        rag_url=rag_url,
        rag_top_k=rag_top_k,
        rag_query=rag_query,
        verbose=args.verbose,
    )
    return 0
