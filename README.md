# KRM Analiz Aracı

KRM ve Findeks raporlarını otomatik analiz eden profesyonel araç.

## 🚀 Hızlı Başlangıç

### Windows Kullanıcıları (EXE)

1. [Releases](https://github.com/helloiamgp/krm-analiz/releases/latest) sayfasından **KRM-Analiz.exe** indirin
2. EXE'yi istediğiniz klasöre kopyalayın
3. KRM PDF dosyalarınızı aynı klasöre veya alt klasörlere yerleştirin
4. **KRM-Analiz.exe**'yi çift tıklayın
5. Raporlar `output/` klasöründe oluşturulur

### Python ile Kullanım

```bash
# Bağımlılıkları kurun
pip install pdfplumber reportlab PyMuPDF pytesseract Pillow rich openpyxl requests

# Scripti çalıştırın
python krm.py
```

## 📋 Gereksinimler

### Temel Gereksinimler
- ✅ **Yok!** EXE kendi başına çalışır

### Findeks Eşleştirmesi İçin (Opsiyonel)
Findeks PDF'lerini KRM ile eşleştirmek istiyorsanız:

**Windows:**
1. [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) indirin
2. Kurulum sırasında "Add to PATH" seçeneğini işaretleyin
3. Bilgisayarı yeniden başlatın

**macOS:**
```bash
brew install tesseract
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

> **Not:** Tesseract kurulu değilse, Findeks eşleştirmesi devre dışı kalır ama KRM analizi normal çalışır.

## ✨ Özellikler

### 🏦 KRM Rapor Analizi
- ✅ Limit ve risk tablolarını otomatik parse et
- ✅ Pasif kaynakları tespit et (180 gün üzeri)
- ✅ Limit aşımları ve anomalileri bul
- ✅ Gecikme tespiti
- ✅ Profesyonel PDF rapor oluştur

### 🔗 Findeks Eşleştirmesi
- ✅ KRM ve Findeks'teki aynı bankaları eşleştir
- ✅ OCR ile Findeks verilerini çıkar
- ✅ Otomatik benzerlik skoru hesapla
- ⚠️ **Tesseract OCR gerektirir**

### 🏦 Logo Çekme (v1.1.0)
- ✅ 56 Türk bankasının logosunu otomatik çek
- ✅ 3 farklı kaynaktan fallback
- ✅ %100 başarı oranı

```bash
python logo_fetcher_simple.py
```

### 📊 Çıktılar
- PDF raporlar (`output/` klasörü)
- Türkçe karakter desteği
- Renk kodlu sorun seviyeleri
- Detaylı kaynak bilgileri

## 📂 Klasör Yapısı

```
your-folder/
├── KRM-Analiz.exe          # Ana uygulama
├── musteri-a/              # Alt klasör (opsiyonel)
│   ├── KRM_rapor.pdf
│   └── Findeks_rapor.pdf
├── musteri-b/              # Başka klasör
│   └── KRM_rapor2.pdf
└── output/                 # Oluşturulur
    ├── musteri-a/
    │   └── KRM_rapor.pdf
    └── musteri-b/
        └── KRM_rapor2.pdf
```

## 🔧 Gelişmiş Kullanım

### Tek PDF Analizi
```bash
python krm.py rapor.pdf
```

### Klasör Bazlı Analiz
```bash
# Tüm alt klasörlerdeki PDF'leri analiz et
python krm.py
```

### Logo Database Güncelleme
```bash
python logo_fetcher_simple.py
```

## 🐛 Sorun Giderme

### "Tesseract is not installed" Hatası
- **Çözüm:** Tesseract kurmanıza gerek yok, sadece Findeks eşleştirmesi çalışmayacak
- **Alternatif:** Yukarıdaki "Findeks Eşleştirmesi İçin" bölümünden Tesseract kurun

### "DLL load failed" (Windows)
- Visual C++ Redistributable kurulumu gerekebilir
- [İndir](https://aka.ms/vs/17/release/vc_redist.x64.exe)

### PDF Açılmıyor
- PDF'in bozuk olmadığından emin olun
- Boyut limiti: 100 MB (varsayılan)

## 📝 Notlar

- Excel dosyası (bankalar listesi) repoda `.gitignore`'da
- Logo database zaman içinde güncellenebilir
- Findeks eşleştirmesi opsiyoneldir
- KRM analizi her zaman çalışır

## 🔗 Bağlantılar

- **Releases:** https://github.com/helloiamgp/krm-analiz/releases
- **Issues:** https://github.com/helloiamgp/krm-analiz/issues
- **Tesseract:** https://github.com/tesseract-ocr/tesseract

---

**Son Güncelleme:** v1.1.0 - Logo çekme sistemi eklendi 🎉
