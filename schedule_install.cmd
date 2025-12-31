@echo off
setlocal

cd /d %~dp0

set TASK_NAME=LocalOpsNotebook Weekly Report
set RUN_SCRIPT=%CD%\scheduled_run_exe.cmd

set START_TIME=09:10

echo [INFO] Installing scheduled task:
echo        Name : "%TASK_NAME%"
echo        Time : Weekly MON %START_TIME%
echo        Run  : "%RUN_SCRIPT%"
echo.

schtasks /Create ^
  /TN "%TASK_NAME%" ^
  /TR "\"%RUN_SCRIPT%\"" ^
  /SC WEEKLY ^
  /D MON ^
  /ST %START_TIME% ^
  /RL LIMITED ^
  /F

if errorlevel 1 (
  echo [ERROR] Failed to create task. Try running CMD as Administrator if your policy blocks creation.
  exit /b 1
)

echo.
echo [OK] Task installed (EXE runner).
echo      Test run: schtasks /Run /TN "%TASK_NAME%"
echo      Check logs under: logs\
echo.
pause
