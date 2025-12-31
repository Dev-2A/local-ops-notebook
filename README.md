# Local Ops Notebook

Windows MVP:
- Scan `notes/` (.md/.txt)
- Fingerprint change detection (changed/unchanged/new/deleted)
- Generate weekly report under `reports/YYYY-Www.md` (Mon~Mon, local time)
- Includes unified diffs using snapshots
- Optional: include Top3 evidence from local-rag-kit server

## Run
```cmd
run.cmd
```

## Output
- Reports are written to: `reports/`
- Local state is stored in: `.ops_state/` (fingerprints + snapshots)

## Weekly Auto Run (Windows Task Scheduler)  
Install:  
```cmd
schedule_install.cmd
```  

Test run immediately:  
```cmd
schtasks /Run /TN "LocalOptNotebook Weekly Report"
```

Logs:
- `logs/scheduled_YYYYMMDD_HHMMSS.log`

Uninstall:
```cmd
schedule_uninstall.cmd
```

## Optional RAG
```cmd
set USE_RAG=1
set RAG_URL=http://127.0.0.1:8000/query
set RAG_TOP_K=3
run.cmd
```