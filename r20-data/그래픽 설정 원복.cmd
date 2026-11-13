@echo off
echo Close RPCS3 before restoring the previous graphics settings.
"%~dp0rpcs3.exe" --headless --tag2-graphics-restore "%~dp0."
if errorlevel 1 (echo Graphics restore failed. Existing backups were retained.) else (echo Previous graphics settings restored. R13 features remain installed.)
pause
