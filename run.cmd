@echo off
setlocal enabledelayedexpansion

cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo [SETUP] Creating venv...
  py -3 -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Failed to create venv. Make sure Python 3 is installed.
    exit /b 1
  )
)

call .venv\Scripts\activate.bat

echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip

echo [SETUP] Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] pip install failed.
  exit /b 1
)

REM Optional overrides:
REM   set USE_RAG=1
REM   set RAG_URL=http://127.0.0.1:8000/query
REM   set RAG_TOP_K=3

echo [RUN] Generating weekly report via config.yaml...
python -m ops_notebook --config config.yaml

if errorlevel 1 (
  echo [ERROR] Report generation failed.
  exit /b 1
)

echo.
echo [DONE] Report generated under reports\ (YYYY-Www.md)
echo.
pause
