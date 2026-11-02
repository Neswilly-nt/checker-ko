@echo off
cd /d "%~dp0.."
start "Checker-ko API" cmd /k "scripts\start-backend.bat"
start "Checker-ko Frontend" cmd /k "scripts\start-frontend.bat"
echo Frontend : http://127.0.0.1:5173
