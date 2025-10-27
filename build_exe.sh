#!/bin/bash
# KRM Analiz Aracı - macOS/Linux Executable Builder
# Bu script PyInstaller kullanarak krm.py'yi çalıştırılabilir dosyaya çevirir

echo "===================================="
echo "KRM Analiz Aracı - EXE Oluşturucu"
echo "===================================="
echo ""

# PyInstaller kurulu mu kontrol et
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "[HATA] PyInstaller kurulu değil!"
    echo ""
    echo "Lütfen önce PyInstaller'ı yükleyin:"
    echo "  pip3 install pyinstaller"
    echo ""
    exit 1
fi

echo "[1/3] PyInstaller kontrol edildi..."

# Eski build dosyalarını temizle
rm -rf build dist krm.spec

echo "[2/3] Eski dosyalar temizlendi..."

# Executable oluştur
echo "[3/3] Executable oluşturuluyor..."
echo ""

pyinstaller --onefile \
    --name="KRM-Analiz" \
    --add-data="fonts:fonts" \
    --console \
    --clean \
    krm.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[HATA] Executable oluşturulamadı!"
    exit 1
fi

echo ""
echo "===================================="
echo "BAŞARILI!"
echo "===================================="
echo ""
echo "Executable dosyası oluşturuldu:"
echo "  dist/KRM-Analiz"
echo ""
echo "Kullanım:"
echo "  1. KRM-Analiz dosyasını istediğiniz dizine kopyalayın"
echo "  2. PDF dosyalarını aynı dizine koyun"
echo "  3. Terminal'de ./KRM-Analiz komutunu çalıştırın"
echo "  4. Raporlar 'output' dizininde oluşacaktır"
echo ""
