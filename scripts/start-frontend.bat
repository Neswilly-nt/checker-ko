@echo off
setlocal
cd /d "%~dp0..\frontend"
if not exist node_modules (
  echo Dependances npm absentes. Lancez scripts\setup-windows.bat en premier.
  exit /b 1
)
call npm run dev
endlocal
