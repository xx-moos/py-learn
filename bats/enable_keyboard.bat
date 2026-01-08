@echo off
title Enable Built-in Keyboard

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting admin rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================
echo Enabling built-in keyboard...
echo ========================================
echo.

:: Enable PS/2 keyboards (built-in) via registry
for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v Start 2^>nul') do (
    echo Found PS/2 keyboard service
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v Start /t REG_DWORD /d 1 /f >nul 2>&1
    if %errorLevel% equ 0 (
        echo Successfully enabled built-in keyboard
    ) else (
        echo Failed to enable keyboard
    )
)

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Note: Restart required for changes to take effect
echo.
pause