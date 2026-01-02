# Changelog
All notable changes to this project will be documented in this file.  

The format is based on Keep a Changelog, and this project follows Semantic Versioning.  

## [0.3.3] - 2026-01-02
### Added
- `--doctor` health check (paths, permissions, optional RAG ping)
- Scheduled EXE runner runs `--doctor` before generating report to fail fast with clear logs

### Changed
- Version bumped to 0.3.3  

## [0.3.2] - 2025-12-31
### Added
- GitHub Actions release workflow: builds Windows onefile EXE via PyInstaller on tag push (`v*`)
- Uploads the built EXE to GitHub Release automatically

### Changed
- Version bumped to 0.3.2  

## [0.3.1] - 2025-12-31
### Added
- `config.yaml` support (YAML) to centralize settings.
- `config.example.yaml` for quick setup.
- Config loader with safe defaults (`ops_notebook/core/config.py`).

### Changed
- `run.cmd`, `scheduled_run.cmd`, and `scheduled_run_exe.cmd` now use `--config config.yaml` by default.
- CLI keeps backward-compatible overrides via flags and env vars.  

## [0.3.0] - 2025-12-31
### Added
- Per-file RAG evidence (Top-K) for this week changed notes
- RAG cache to avoid repeated calls (`.ops_state/rag_cache.json`)
- local-rag-kit `/query` compatible parsing (`chunks` + `doc` + `text`)

### Changed
- RAG section in report switched from global Top-K to per-file Top-K  

## [0.2.3] - 2025-12-31
### Added
- One-file Windows EXE build via PyInstaller (`build_exe.cmd`)
- Scheduled task runner switched to EXE (`scheduled_run_exe.cmd`)
- PyInstaller data bundling for templates

### Changed
- Version bumped to 0.2.3  

## [0.2.2] - 2025-12-31  
### Added  
- GitHub Actions CI (Windows runner): ruff + pytest  
- Dev dependencies (`dev-requirements.txt`)  
- Minimal test for weekly report generation  

### Changed  
- Version bumped to 0.2.2  

## [0.2.1] - 2025-12-31  
### Added  
- Windows Task Scheduler integration:  
  - `scheduled_run.cmd` (non-interactive scheduled entrypoint with logs)  
  - `schedule_install.cmd` / `schedule_uninstall.cmd`  
- Scheduled run logs under `logs/` (ignored by git)  

### Changed  
- Version bumped to 0.2.1  

## [0.2.0] - 2025-12-30  
### Added  
- Weekly reports are now saved under `reports/YYYY-Www.md` (Mon~Mon, local time).  
- Unified diff section per changed file (snapshot-based).  
- Snapshot store under `.ops_state/snapshots/` to support diffs.  
- LICENSE (MIT) and this CHANGELOG.  

### Changed
- `run.cmd` now generates reports into the `reports/` directory by default.  
- `.gitignore` no longer ignores the generated reports directory (reports can be committed if desired).  

## [0.1.0] - 2025-12-30  
### Added  
- Notes scanning (`notes/`) with fingerprint change detection.  
- Weekly report generation from template.  
- Optional RAG evidence section (Top-K) via local-rag-kit endpoint.  