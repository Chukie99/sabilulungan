@echo off
cd /d "%~dp0"
python check_gateway.py
if errorlevel 1 (echo [FAIL] Tes belum lolos.) else (echo [PASS] Semua pemeriksaan lolos.)
pause
