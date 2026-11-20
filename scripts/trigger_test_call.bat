@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0trigger_test_call.ps1" %*
echo.
pause
