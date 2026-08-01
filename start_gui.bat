@echo off
setlocal
cd /d "%~dp0"
set "PATH=D:\platform-tools-latest-windows\platform-tools;%PATH%"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" "%~dp0main.py"
    exit /b 0
)

if exist "..\.venv\Scripts\pythonw.exe" (
    start "" "..\.venv\Scripts\pythonw.exe" "%~dp0main.py"
    exit /b 0
)

where pythonw.exe >nul 2>nul
if %errorlevel% equ 0 (
    start "" pythonw.exe "%~dp0main.py"
    exit /b 0
)

python.exe "%~dp0main.py"
