# Changelog
All notable changes to this project will be documented in this file.  

The format is based on Keep a Changelog, and this project follows Semantic Versioning.  

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