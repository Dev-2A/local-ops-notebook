@echo off
setlocal

set TASK_NAME=LocalOpsNotebook Weekly Report

echo [INFO] Removing scheduled task: "%TASK_NAME%"
schtasks /Delete /TN "%TASK_NAME%" /F

if errorlevel 1 (
  echo [ERROR] Failed to delete task (maybe it doesn't exist).
  exit /b 1
)

echo [OK] Task removed.
pause
