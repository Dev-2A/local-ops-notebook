@echo off
setlocal enabledelayedexpansion

cd /d %~dp0

if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set LOG_FILE=logs\scheduled_%TS%.log

echo [INFO] Local Ops Notebook scheduled run started > "%LOG_FILE%"
echo [INFO] Repo: %CD% >> "%LOG_FILE%"

if not exist .venv\Scripts\python.exe (
  echo [SETUP] Creating venv... >> "%LOG_FILE%"
  py -3 -m venv .venv >> "%LOG_FILE%" 2>&1
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. >> "%LOG_FILE%"
    exit /b 1
  )
)

call .venv\Scripts\activate.bat >> "%LOG_FILE%" 2>&1

echo [SETUP] Installing requirements... >> "%LOG_FILE%"
pip install -r requirements.txt >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] pip install failed. >> "%LOG_FILE%"
  exit /b 1
)

echo [RUN] Generating weekly report via config.yaml... >> "%LOG_FILE%"
python -m ops_notebook --config config.yaml >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
  echo [ERROR] Report generation failed. >> "%LOG_FILE%"
  exit /b 1
)

echo [OK] Completed. >> "%LOG_FILE%"
exit /b 0
