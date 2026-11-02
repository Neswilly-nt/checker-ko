@echo off
setlocal
cd /d "%~dp0..\backend"
if not exist .venv\Scripts\python.exe (
  echo [1/3] Creation d'un environnement Python...
  py -3 -m venv .venv
  if errorlevel 1 exit /b 1
)
echo [2/3] Installation des dependances backend...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 exit /b 1
echo [3/3] Verification des dependances frontend...
cd /d "%~dp0..\frontend"
call npm install
if errorlevel 1 exit /b 1
echo Installation terminee. Aucun GitHub ni compte cloud requis.
endlocal
