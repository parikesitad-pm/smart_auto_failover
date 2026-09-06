@echo off
:: ============================================================================
:: MODULA - Smart Auto Failover - Administrator Launcher
:: Automatically requests UAC elevation if not already running as Admin
:: ============================================================================

net session >nul 2>&1
if %errorLevel% == 0 (
    goto :run_app
) else (
    goto :elevate
)

:elevate
echo Requesting Windows Administrator Privileges for MODULA...
powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process cmd -ArgumentList '/c \"\"%~f0\"\"' -Verb RunAs"
exit /b

:run_app
cd /d "%~dp0"
echo Starting MODULA - Smart Auto Failover with Administrator rights...
python main.py
if %errorLevel% neq 0 (
    echo.
    echo Application exited with code %errorLevel%.
    pause
)
