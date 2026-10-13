@echo off
cd /d "%~dp0"
python check_media.py
set "SABIL_MEDIA_RESULT=%ERRORLEVEL%"
if "%SABIL_MEDIA_RESULT%"=="0" (echo [PASS] TTS dan render lolos.) else (echo [FAIL] Tes media belum lolos.)
pause
exit /b %SABIL_MEDIA_RESULT%
