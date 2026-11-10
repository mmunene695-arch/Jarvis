@echo off
REM JARVIS v0.2 - Windows installer wrapper for install-windows.ps1
REM Usage:  install-windows.cmd            (all optional extras)
REM         install-windows.cmd voice      (only the voice extra)
setlocal

set "HERE=%~dp0"
set "EXTRAS=%~1"
if "%EXTRAS%"=="" set "EXTRAS=all"

where powershell >nul 2>nul
if errorlevel 1 (
    echo PowerShell was not found. Install Python 3.9+ and run install-windows.ps1 manually.
    exit /b 1
)

echo Starting the JARVIS installer in PowerShell...
powershell -NoProfile -ExecutionPolicy Bypass -File "%HERE%install-windows.ps1" -Extras "%EXTRAS%"
set "CODE=%ERRORLEVEL%"

if not "%CODE%"=="0" (
    echo.
    echo Installation did not finish cleanly ^(exit code %CODE%^).
    echo See the messages above, then check INSTALL.md.
) else (
    echo.
    echo Installation complete.
)
exit /b %CODE%
