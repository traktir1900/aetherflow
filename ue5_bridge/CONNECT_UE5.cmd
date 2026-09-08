@echo off
setlocal
cd /d "%~dp0"
python preset_cli.py --preset AetherFlowRemote --function AetherFlow_Test
set ERR=%ERRORLEVEL%
echo.
if %ERR% EQU 0 (
  echo AetherFlow UE5 connection test PASSED.
) else (
  echo AetherFlow UE5 connection test FAILED with code %ERR%.
)
pause
exit /b %ERR%
