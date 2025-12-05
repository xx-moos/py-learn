@echo off
title Disable Built-in Keyboard

:: Check admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Requesting admin rights...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================
echo Disabling built-in keyboard...
echo ========================================
echo.

:: Disable PS/2 keyboards (built-in) via registry
for /f "tokens=*" %%i in ('reg query "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v Start 2^>nul') do (
    echo Found PS/2 keyboard service
    reg add "HKLM\SYSTEM\CurrentControlSet\Services\i8042prt" /v Start /t REG_DWORD /d 4 /f >nul 2>&1
    if %errorLevel% equ 0 (
        echo Successfully disabled built-in keyboard
    ) else (
        echo Failed to disable keyboard
    )
)

echo.
echo ========================================
echo Done!
echo ========================================
echo.
echo Note: 
echo - Restart required for changes to take effect
echo - USB keyboards are NOT affected
echo - Run enable_keyboard.bat to re-enable
echo.
pause