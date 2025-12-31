import argparse
import os
from pathlib import Path

from ops_notebook.core.report import generate_weekly_report


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return v.strip().lower() in ("1", "true", "yes", "y", "on")


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="ops_notebook",
        description="Local Ops Notebook - fingerprint change detection + weekly report",
    )
    parser.add_argument("--notes", default="notes", help="Notes folder (default: notes)")
    parser.add_argument("--template", default="templates/weekly_report_template.md", help="Template path")
    
    parser.add_argument("--reports-dir", default="reports", help="Reports directory (default: reports)")
    parser.add_argument(
        "--report",
        default="",
        help="Output report path (optional). If empty, uses reports/YYYY-Www.md",
    )
    
    parser.add_argument("--state", default=".ops_state/fingerprints.json", help="State json path")
    
    parser.add_argument("--use-rag", action="store_true", help="Enable RAG evidence (override USE_RAG env)")
    parser.add_argument("--rag-url", default=os.getenv("RAG_URL", "http://127.0.0.1:8000/query"), help="RAG server URL")
    parser.add_argument("--rag-top-k", type=int, default=int(os.getenv("RAG_TOP_K", "3")), help="RAG top-k")
    parser.add_argument("--rag-query", default=os.getenv("RAG_QUERY", ""), help="Custom query for RAG")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    use_rag = args.use_rag or _env_bool("USE_RAG", False)
    
    notes_dir = Path(args.notes)
    template_path = Path(args.template)
    state_path = Path(args.state)
    
    reports_dir = Path(args.reports_dir)
    report_path = Path(args.report) if args.report.strip() else None
    
    reports_dir.mkdir(parents=True, exist_ok=True)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    generate_weekly_report(
        notes_dir=notes_dir,
        reports_dir=reports_dir,
        report_path=report_path,
        template_path=template_path,
        state_path=state_path,
        use_rag=use_rag,
        rag_url=args.rag_url,
        rag_top_k=args.rag_top_k,
        rag_query=args.rag_query.strip(),
        verbose=args.verbose,
    )
    return 0