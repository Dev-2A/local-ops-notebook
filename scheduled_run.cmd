@echo off
setlocal enabledelayedexpansion

REM ===== Repo root =====
cd /d %~dp0

REM ===== Settings (override via environment if needed) =====
set NOTES_DIR=notes
set REPORTS_DIR=reports
set TEMPLATE_PATH=templates\weekly_report_template.md
set STATE_PATH=.ops_state\fingerprints.json

REM Optional RAG (default: off)
REM You can enable by setting USE_RAG=1 as a machine/user environment variable,
REM or uncomment below lines.
REM set USE_RAG=1
REM set RAG_URL=http://127.0.0.1:8000/query
REM set RAG_TOP_K=3

REM ===== Log file =====
if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set LOG_FILE=logs\scheduled_%TS%.log

echo [INFO] Local Ops Notebook scheduled run started > "%LOG_FILE%"
echo [INFO] Repo: %CD% >> "%LOG_FILE%"

REM ===== Ensure venv exists =====
if not exist .venv\Scripts\python.exe (
  echo [SETUP] Creating venv... >> "%LOG_FILE%"
  py -3 -m venv .venv >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. >> "%LOG_FILE%"
    exit /b 1
  )

  echo [SETUP] Installing requirements... >> "%LOG_FILE%"
  call .venv\Scripts\activate.bat >> "%LOG_FILE%" 2>&1
  pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    echo [ERROR] pip install failed. >> "%LOG_FILE%"
    exit /b 1
  )
) else (
  call .venv\Scripts\activate.bat >> "%LOG_FILE%" 2>&1
)

REM ===== Run report generation =====
echo [RUN] Generating weekly report... >> "%LOG_FILE%"
python -m ops_notebook ^
  --notes "%NOTES_DIR%" ^
  --template "%TEMPLATE_PATH%" ^
  --reports-dir "%REPORTS_DIR%" ^
  --state "%STATE_PATH%" >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
  echo [ERROR] Report generation failed. >> "%LOG_FILE%"
  exit /b 1
)

echo [OK] Completed. >> "%LOG_FILE%"
exit /b 0
