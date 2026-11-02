@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist .venv\Scripts\python.exe (
  echo Python non installe pour ce projet. Lancez scripts\setup-windows.bat en premier.
  exit /b 1
)
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
endlocal
