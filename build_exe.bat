@echo off
REM KRM Analiz Aracı - Windows EXE Builder
REM Bu script PyInstaller kullanarak krm.py'yi exe dosyasına çevirir

echo ====================================
echo KRM Analiz Araci - EXE Olusturucu
echo ====================================
echo.

REM PyInstaller kurulu mu kontrol et
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo [HATA] PyInstaller kurulu degil!
    echo.
    echo Lutfen once PyInstaller'i yukleyin:
    echo   pip install pyinstaller
    echo.
    pause
    exit /b 1
)

echo [1/3] PyInstaller kontrol edildi...

REM Eski build dosyalarını temizle
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist krm.spec del krm.spec

echo [2/3] Eski dosyalar temizlendi...

REM EXE oluştur
echo [3/3] EXE olusturuluyor...
echo.

pyinstaller --onefile ^
    --name="KRM-Analiz" ^
    --add-data="fonts;fonts" ^
    --icon=NONE ^
    --console ^
    --clean ^
    krm.py

if errorlevel 1 (
    echo.
    echo [HATA] EXE olusturulamadi!
    pause
    exit /b 1
)

echo.
echo ====================================
echo BASARILI!
echo ====================================
echo.
echo EXE dosyasi olusturuldu:
echo   dist\KRM-Analiz.exe
echo.
echo Kullanim:
echo   1. KRM-Analiz.exe dosyasini istediginiz dizine kopyalayin
echo   2. PDF dosyalarini ayni dizine koyun
echo   3. KRM-Analiz.exe'yi cift tiklayarak calistirin
echo   4. Raporlar "output" dizininde olusacaktir
echo.
pause
