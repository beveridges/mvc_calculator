@echo off
REM Quick MSI Dialog Preview Script
REM This compiles a minimal WXS to test dialog images quickly

echo Building test MSI for dialog preview...
echo.

REM Update paths in preview_msi_dialog.wxs first!
candle preview_msi_dialog.wxs
if %errorlevel% neq 0 (
    echo ERROR: Candle failed!
    pause
    exit /b 1
)

light -ext WixUIExtension preview_msi_dialog.wixobj -o test_dialog.msi
if %errorlevel% neq 0 (
    echo ERROR: Light failed!
    pause
    exit /b 1
)

echo.
echo SUCCESS! Test MSI created: test_dialog.msi
echo Run it to preview the dialog images.
echo.
pause

