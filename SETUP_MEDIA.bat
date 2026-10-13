@echo off
cd /d "%~dp0"
python -m pip install -r requirements_media.txt
if errorlevel 1 goto failed
where ffmpeg >nul 2>nul
if errorlevel 1 goto ffmpeg
where ffprobe >nul 2>nul
if errorlevel 1 goto ffmpeg
python -c "from media_tools import status; import json; print(json.dumps(status(),indent=2))"
pause
exit /b 0
:ffmpeg
echo FFmpeg dan ffprobe belum ada di PATH. Jalankan:
echo winget install --id Gyan.FFmpeg --exact
echo Setelah instalasi, tutup CMD lalu buka lagi dan ulang SETUP_MEDIA.bat.
pause
exit /b 1
:failed
echo Instalasi dependensi gagal. Periksa output di atas.
pause
exit /b 1
