from pathlib import Path
import shutil

from ops_notebook.core.report import generate_weekly_report


def test_generate_weekly_report(tmp_path: Path):
    # Arrange: temp project structure
    notes_dir = tmp_path / "notes"
    reports_dir = tmp_path / "reports"
    template_dir = tmp_path / "templates"
    state_dir = tmp_path / ".ops_state"
    
    notes_dir.mkdir(parents=True)
    reports_dir.mkdir(parents=True)
    template_dir.mkdir(parents=True)
    state_dir.mkdir(parents=True)
    
    (notes_dir / "a.md").write_text("# A\nhello\n", encoding="utf-8")
    
    template = (
        "# Weekly Ops Report ({week_range})\n\n"
        "Generated: {generated_at}\n"
        "Report File: {report_file}\n\n"
        "## 1) This week changed files\n{changed_files_block}\n"
        "## 2) File diffs (unified diff)\n{diff_block}\n"
        "## 3) Auto digest (template-based)\n{auto_digest_block}\n"
        "## 4) RAG evidence (Top {rag_top_k})\n{rag_evidence_block}\n"
    )
    (template_dir / "weekly_report_template.md").write_text(template, encoding="utf-8")
    
    # Act
    generate_weekly_report(
        notes_dir=notes_dir,
        reports_dir=reports_dir,
        report_path=None,   # auto path
        template_path=template_dir / "weekly_report_template.md",
        state_path=state_dir / "fingerprints.json",
        use_rag=False,
        rag_url="http://127.0.0.1:8000/query",
        rag_top_k=3,
        rag_query="",
        verbose=False,
    )
    
    # Assert: report exists and contains expected sections
    report_files = list(reports_dir.glob("*.md"))
    assert len(report_files) == 1
    
    body = report_files[0].read_text(encoding="utf-8")
    assert "Weekly Ops Report" in body
    assert "This week changed files" in body
    assert "File diffs" in body
    assert "Auto digest" in body
    
    # Act 2: change note -> run again -> should still generate
    (notes_dir / "a.md").write_text("# A\nhello changed\n", encoding="utf-8")

    generate_weekly_report(
        notes_dir=notes_dir,
        reports_dir=reports_dir,
        report_path=None,
        template_path=template_dir / "weekly_report_template.md",
        state_path=state_dir / "fingerprints.json",
        use_rag=False,
        rag_url="http://127.0.0.1:8000/query",
        rag_top_k=3,
        rag_query="",
        verbose=False,
    )

    report_files2 = list(reports_dir.glob("*.md"))
    assert len(report_files2) == 1
    body2 = report_files2[0].read_text(encoding="utf-8")
    assert "diff" in body2  # code-fence header inside report