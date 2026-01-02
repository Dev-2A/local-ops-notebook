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

REM Doctor first (quick health check)
dist\local-ops-notebook.exe --config config.yaml --doctor >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] Doctor failed. Abort report generation. >> "%LOG_FILE%"
  exit /b 1
)

dist\local-ops-notebook.exe --config config.yaml >> "%LOG_FILE%" 2>&1
if errorlevel 1 (
  echo [ERROR] EXE report generation failed. >> "%LOG_FILE%"
  exit /b 1
)

echo [OK] Completed. >> "%LOG_FILE%"
exit /b 0
