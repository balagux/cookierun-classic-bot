@echo off
setlocal
cd /d "%~dp0"

if exist "..\.venv\Scripts\python.exe" (
    "..\.venv\Scripts\python.exe" build_exe.py
) else if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" build_exe.py
) else (
    python.exe build_exe.py
)

if errorlevel 1 (
    echo.
    echo Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete: dist\CookieRunClassicBot.exe
pause
