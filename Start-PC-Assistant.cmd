@echo off
setlocal
cd /d "%~dp0"
title AI Love Strategist PC Assistant
python -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 goto use_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)" >nul 2>&1
if not errorlevel 1 goto use_py
if not exist "%~dp0.venv\Scripts\python.exe" goto missing
"%~dp0.venv\Scripts\python.exe" "%~dp0desktop\start.py"
goto result
:use_python
python "%~dp0desktop\start.py"
goto result
:use_py
py -3 "%~dp0desktop\start.py"
goto result
:missing
echo Python 3.11 or newer is required.
pause
exit /b 1
:result
if errorlevel 1 pause
endlocal
