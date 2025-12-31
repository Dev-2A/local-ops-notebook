@echo off
setlocal

cd /d %~dp0

if not exist .venv\Scripts\python.exe (
  echo [SETUP] Creating venv...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

echo [SETUP] Installing deps...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install -r dev-requirements.txt

echo [BUILD] PyInstaller onefile build...
pyinstaller --noconfirm --clean --onefile ^
  --name local-ops-notebook ^
  --add-data "templates;templates" ^
  ops_notebook_entry.py

if errorlevel 1 (
  echo [ERROR] Build failed.
  exit /b 1
)

echo.
echo [OK] Build done.
echo      Output: dist\local-ops-notebook.exe
echo.
pause
