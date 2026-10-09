@echo off
cd /d %~dp0
echo [STARTING] Virtual Office Dashboard...
start "" "http://127.0.0.1:5050"
python dashboard.py
pause
