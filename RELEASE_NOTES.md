# KRM Analiz Aracı - Sürüm Notları

## 📥 İndirme

**Windows Kullanıcıları:**
- [KRM-Analiz.exe](https://github.com/helloiamgp/krm-analiz/releases/latest) dosyasını indirin
- Çift tıklayın ve kullanmaya başlayın

---

## v1.0.0 - İlk Sürüm (27 Ekim 2025)

### 🎉 İlk Stabil Sürüm

KRM Analiz Aracı'nın ilk stabil sürümü yayınlandı!

### ✨ Özellikler

#### PDF Analiz
- ✅ TBB KRM PDF raporlarından otomatik veri çıkarma
- ✅ Limit ve risk bilgilerinin parsing'i
- ✅ Firma ve rapor tarihi tespiti

#### Anomali Tespiti (6 Senaryo)
1. **Nakdi Limit Aşımı** (WARNING/CRITICAL)
2. **Gayrinakdi Limit Aşımı** (WARNING/CRITICAL)
3. **Limitsiz Kullanım** (CRITICAL)
4. **Gecikme Tespiti** (30+ gün CRITICAL)
5. **Toplam Limit Aşımı** (CRITICAL)
6. **Yüksek Kullanım** (>95% WARNING)

#### Pasif Kaynak Tespiti
- 180+ gün eski revize tarihi
- Sıfır limit ve sıfır risk kontrolü
- Otomatik filtreleme

#### Raporlama
- 📊 Profesyonel PDF çıktıları
- 🎨 Renkli tablolar (kritik: kırmızı, uyarı: turuncu)
- 📈 Özet istatistikler
- 📋 Detaylı kaynak bilgileri
- 🖼️ Türkçe karakter desteği (DejaVu Sans font)

#### Kullanıcı Arayüzü
- 🎨 Renkli terminal çıktısı (Rich library)
- 📊 Zebra-stripe tablolar
- ⚡ Progress bar desteği
- 💬 Türkçe kullanıcı mesajları

### 🔧 Teknik Özellikler

- **Dil:** Python 3.8+
- **Bağımlılıklar:** pdfplumber, reportlab, rich, pyinstaller
- **Platform:** Windows, macOS, Linux
- **Mimari:** Type hints, Google Style docstrings
- **Kod Kalitesi:** DRY prensibi, constants, error handling

### 📦 Dağıtım

#### Windows Kullanıcıları (Önerilen)
- **KRM-Analiz.exe** - Tek dosya, hazır kullanım
- Python kurulumu gerektirmez
- Çift tıklama ile çalışır

#### Geliştiriciler / Python Kullanıcıları
- **Kaynak kod:** GitHub repository
- `pip install -r requirements.txt`
- `python3 krm.py`

### 🐛 Bilinen Sorunlar

- Windows Defender/SmartScreen false-positive uyarısı verebilir (PyInstaller bilinen sorunu)
- PDF formatı değişirse kod güncellemesi gerekebilir

### 📝 Dokümantasyon

- ✅ README.md - Genel kullanım kılavuzu
- ✅ EXE_KULLANIM.txt - Windows exe detaylı kılavuz
- ✅ KULLANIM.txt - Python script kullanımı
- ✅ Kod içi docstring'ler

### 🙏 Teşekkürler

- TBB KRM rapor formatı
- pdfplumber kütüphanesi geliştiricileri
- ReportLab PDF üretim araçları
- Rich terminal rendering kütüphanesi

---

## Gelecek Sürümler İçin Planlar

### v1.1.0 (Planlanan)
- [ ] Excel çıktı desteği
- [ ] Toplu analiz özet raporu
- [ ] E-posta bildirimi (isteğe bağlı)

### v1.2.0 (Planlanan)
- [ ] Web arayüzü (Next.js)
- [ ] Supabase entegrasyonu
- [ ] Gerçek zamanlı dashboard

### v2.0.0 (Planlanan)
- [ ] GRC sistem entegrasyonu
- [ ] BDDK BVTS otomatik raporlama
- [ ] TBB Risk Merkezi API entegrasyonu

---

## İletişim

- **GitHub:** https://github.com/helloiamgp/krm-analiz
- **Issues:** https://github.com/helloiamgp/krm-analiz/issues
- **Yazar:** helloiamgp
