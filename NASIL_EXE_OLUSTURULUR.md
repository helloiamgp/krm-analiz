# EXE Oluşturma Kılavuzu (Geliştirici İçin)

Bu kılavuz, KRM Analiz Aracı için Windows EXE dosyası oluşturmak isteyenler içindir.

## 🔧 Gereksinimler

- Python 3.8 veya üstü
- Windows işletim sistemi (EXE oluşturmak için)

## 📦 Adım Adım

### 1. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

Bu komut şunları yükler:
- pdfplumber
- reportlab
- rich
- pyinstaller

### 2. EXE Oluştur

```bash
pyinstaller --onefile --name="KRM-Analiz" --add-data="fonts;fonts" --console --clean krm.py
```

**Parametreler:**
- `--onefile`: Tek dosya EXE oluştur
- `--name`: Çıktı dosya adı
- `--add-data`: fonts klasörünü dahil et (Türkçe karakter desteği)
- `--console`: Terminal penceresi göster
- `--clean`: Eski build dosyalarını temizle

### 3. EXE'yi Bul

EXE dosyası şurada oluşur:
```
dist/KRM-Analiz.exe
```

### 4. Test Et

```bash
cd dist
KRM-Analiz.exe
```

## 📤 GitHub'a Yükleme

### Yöntem 1: GitHub Web Arayüzü (Kolay)

1. https://github.com/helloiamgp/krm-analiz/releases sayfasına git
2. **"Draft a new release"** tıkla
3. **Tag:** `v1.0.0` yaz ve "Create new tag" seç
4. **Title:** `v1.0.0 - İlk Sürüm`
5. **Description:** RELEASE_NOTES.md'den kopyala
6. **Attach files:** `dist/KRM-Analiz.exe` dosyasını sürükle
7. **Publish release** tıkla

### Yöntem 2: GitHub CLI (Hızlı)

```bash
# EXE'yi oluştur
pyinstaller --onefile --name="KRM-Analiz" --add-data="fonts;fonts" --console --clean krm.py

# Tag oluştur ve push et
git tag -a v1.0.0 -m "İlk sürüm"
git push origin v1.0.0

# Release oluştur ve EXE'yi yükle
gh release create v1.0.0 dist/KRM-Analiz.exe --title "v1.0.0 - İlk Sürüm" --notes-file RELEASE_NOTES.md
```

## ⚠️ Önemli Notlar

### Windows Defender Uyarısı
PyInstaller ile oluşturulan EXE dosyaları bazen false-positive tetikler. Bu normal bir durumdur.

### Dosya Boyutu
EXE dosyası ~50-100 MB olacaktır çünkü:
- Python runtime dahil
- Tüm bağımlılıklar (pdfplumber, reportlab, rich) dahil
- fonts/ klasörü dahil

### macOS/Linux
Bu kılavuz sadece Windows için geçerlidir. macOS/Linux için PyInstaller aynı şekilde çalışır ama:
- `--add-data` parametresi farklı: `"fonts:fonts"` (noktalı virgül yerine iki nokta)
- Çıktı `.exe` değil, binary dosya olur

## 🐛 Sorun Giderme

### Hata: "Module not found"
```bash
pip install -r requirements.txt
```

### Hata: "Font bulunamadı"
`fonts/` klasörünün mevcut olduğundan emin olun:
```
fonts/
├── DejaVuSans.ttf
└── DejaVuSans-Bold.ttf
```

### EXE Çalışmıyor
`--console` parametresi ile oluşturun ve terminal çıktısını inceleyin.

## 📚 Kaynaklar

- [PyInstaller Dokümantasyonu](https://pyinstaller.org/)
- [GitHub Releases Kılavuzu](https://docs.github.com/en/repositories/releasing-projects-on-github)
