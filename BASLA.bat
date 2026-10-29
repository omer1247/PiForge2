@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo PiForge icin gereken kutuphane kontrol ediliyor...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Kurulum basarisiz. Python ve internet baglantisini kontrol et.
  pause
  exit /b 1
)
echo.
echo PiForge baslatiliyor...
python app.py
pause
