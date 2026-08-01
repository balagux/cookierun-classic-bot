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

if errorlevel 1 goto :failed

set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC%" set "ISCC=C:\Program Files\Inno Setup 6\ISCC.exe"

if not exist "%ISCC%" (
    echo Inno Setup Compiler was not found.
    echo Install it with: winget install --id JRSoftware.InnoSetup
    goto :failed
)

"%ISCC%" installer.iss
if errorlevel 1 goto :failed

echo.
echo Installer complete: installer\CookieRunClassicBot-Setup.exe
pause
exit /b 0

:failed
echo.
echo Installer build failed.
pause
exit /b 1
