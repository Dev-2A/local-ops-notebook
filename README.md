# Local Ops Notebook

Windows MVP:
- Scan `notes/` (.md/.txt)
- Fingerprint change detection (changed/unchanged/new/deleted)
- Generate `weekly_report.md` for this week (Mon-Sun)
- Optional: include Top3 evidence from local-rag-kit server

## Run
```cmd
run.cmd
```

## Optional RAG
```cmd
set USE_RAG=1
set RAG_URL=http://127.0.0.1:8000/query
set RAG_TOP_K=3
run.cmd
```