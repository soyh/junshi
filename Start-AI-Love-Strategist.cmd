@echo off
setlocal
cd /d "%~dp0"
title AI Love Strategist
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Python environment not found.
  echo Complete the Windows installation steps in README.md first.
  echo Expected: .venv\Scripts\python.exe
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0scripts\start_local.py"
if errorlevel 1 (
  echo.
  echo Startup failed. Keep the error above for troubleshooting.
  pause
  exit /b 1
)
endlocal
