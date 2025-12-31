# Weekly Ops Report ({week_range})  

Generated: {generated_at}  
Report File: {report_file}  

## 1) This week changed files  
{changed_files_block}  

## 2) File diffs (unified diff)  
{diff_block}  

## 3) Auto digest (template-based)  
{auto_digest_block}  

## 4) RAG evidence per changed file (Top {rag_top_k})  
{rag_per_file_block}  

---  
Notes:  
- This report is generated automatically from `notes/` using fingerprints + snapshots.  
- Week 기준: Monday 00:00 ~ next Monday 00:00 (local time).  