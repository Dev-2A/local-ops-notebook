@echo off
setlocal enabledelayedexpansion
cd /d %~dp0

if not exist logs mkdir logs
for /f %%i in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TS=%%i
set LOG_FILE=logs\scheduled_exe_%TS%.log

echo [INFO] Scheduled EXE run started > "%LOG_FILE%"
echo [INFO] Repo: %CD% >> "%LOG_FILE%"

if not exist dist\local-ops-notebook.exe (
  echo [ERROR] dist\local-ops-notebook.exe not found. Run build_exe.cmd first. >> "%LOG_FILE%"
  exit /b 1
)

REM exe runs from repo root so relative paths work.
dist\local-ops-notebook.exe ^
  --notes notes ^
  --template templates\weekly_report_template.md ^
  --reports-dir reports ^
  --state .ops_state\fingerprints.json >> "%LOG_FILE%" 2>&1

if errorlevel 1 (
  echo [ERROR] EXE report generation failed. >> "%LOG_FILE%"
  exit /b 1
)

echo [OK] Completed. >> "%LOG_FILE%"
exit /b 0
