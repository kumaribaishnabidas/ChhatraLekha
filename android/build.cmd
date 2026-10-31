@echo off
REM Thin CMD shim around build.ps1 so the build can be launched without
REM PowerShell execution-policy friction. See build.ps1 for details.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build.ps1" %*
exit /b %ERRORLEVEL%
