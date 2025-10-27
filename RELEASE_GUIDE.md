# GitHub Release Oluşturma Kılavuzu

Bu kılavuz, KRM Analiz Aracı için yeni bir release oluşturmak isteyen geliştiriciler içindir.

## 📋 Ön Hazırlık

### 1. Kod Değişiklikleri Tamamlanmalı
- [ ] Tüm özellikler test edilmiş
- [ ] Buglar düzeltilmiş
- [ ] Dokümantasyon güncel
- [ ] Git commit'leri temiz

### 2. Sürüm Numarası Belirle
[Semantic Versioning](https://semver.org/) kullanıyoruz:
- **MAJOR.MINOR.PATCH** (örn: 1.2.3)
- **MAJOR:** Breaking changes (API değişiklikleri)
- **MINOR:** Yeni özellikler (backward compatible)
- **PATCH:** Bug fixes

## 🚀 Release Oluşturma Adımları

### Yöntem 1: Otomatik Build (GitHub Actions)

#### Adım 1: Git Tag Oluştur
```bash
# Versiyon numarasını belirle (örn: v1.0.0)
git tag -a v1.0.0 -m "İlk stabil sürüm"

# Tag'i GitHub'a push et
git push origin v1.0.0
```

#### Adım 2: GitHub Actions Bekle
1. GitHub repository'ye git
2. **Actions** sekmesine tıkla
3. "Build Windows EXE" workflow'unun çalıştığını gör
4. ~5-10 dakika bekle
5. Workflow tamamlandığında otomatik olarak Release oluşur

#### Adım 3: Release Kontrol Et
1. GitHub repository'de **Releases** sekmesine git
2. Yeni release'i gör
3. **KRM-Analiz.exe** dosyasının eklenmiş olduğunu kontrol et
4. Release notes'u düzenle (isteğe bağlı)

### Yöntem 2: Manuel Build (Windows PC Gerekli)

#### Adım 1: EXE Oluştur
```cmd
# Windows PC'de
cd C:\path\to\KRM
build_exe.bat

# dist\KRM-Analiz.exe oluşur
```

#### Adım 2: Git Tag Oluştur
```bash
git tag -a v1.0.0 -m "İlk stabil sürüm"
git push origin v1.0.0
```

#### Adım 3: GitHub Release Oluştur (Manuel)
1. GitHub repository'ye git
2. **Releases** → **Draft a new release** tıkla
3. **Tag:** v1.0.0 seç
4. **Title:** "KRM Analiz Aracı v1.0.0"
5. **Description:** RELEASE_NOTES.md'den kopyala
6. **Attach files:** dist\KRM-Analiz.exe dosyasını sürükle
7. **Publish release** tıkla

## 📝 Release Notes Şablonu

```markdown
## KRM Analiz Aracı v1.0.0

### 🎉 Yeni Özellikler
- [Özellik 1 açıklaması]
- [Özellik 2 açıklaması]

### 🐛 Düzeltilen Hatalar
- [Hata 1 açıklaması]
- [Hata 2 açıklaması]

### 📦 İndirme
**Windows Kullanıcıları:**
- KRM-Analiz.exe dosyasını indirin
- Çift tıklayın ve kullanmaya başlayın

**Python Kullanıcıları:**
- Kaynak kodu indirin
- `pip install -r requirements.txt`
- `python3 krm.py`

### ⚠️ Önemli Notlar
- Windows Defender uyarısı alabilirsiniz
- "Yine de çalıştır" seçeneğini tıklayın

### 🔧 Sistem Gereksinimleri
- Windows 10/11 (64-bit)
- En az 100 MB boş disk alanı
```

## 🔄 Güncelleme Süreci

### Minor/Patch Update (1.0.0 → 1.1.0)
```bash
# 1. Değişiklikleri commit et
git add .
git commit -m "feat: yeni özellik eklendi"

# 2. Tag oluştur
git tag -a v1.1.0 -m "Yeni özellikler"
git push origin main
git push origin v1.1.0

# 3. GitHub Actions otomatik build yapar
```

### Major Update (1.9.9 → 2.0.0)
```bash
# 1. Breaking changes varsa CHANGELOG.md'yi güncelle
# 2. README.md'yi güncelle
# 3. Migration guide ekle (gerekiyorsa)

git tag -a v2.0.0 -m "Major release - breaking changes"
git push origin main
git push origin v2.0.0
```

## ✅ Release Checklist

Release yapmadan önce:

- [ ] Tüm testler geçti
- [ ] README.md güncel
- [ ] RELEASE_NOTES.md güncellendi
- [ ] Versiyon numarası belirlendi
- [ ] Git commit'leri temiz
- [ ] Tag mesajı açıklayıcı
- [ ] GitHub Actions workflow çalışıyor
- [ ] EXE dosyası test edildi (Windows PC'de)

## 🐛 Sorun Giderme

### Problem: GitHub Actions başlamıyor
**Çözüm:**
- Tag'in `v` ile başladığından emin ol (örn: `v1.0.0`)
- `.github/workflows/build-exe.yml` dosyasının doğru olduğunu kontrol et

### Problem: PyInstaller hatası
**Çözüm:**
- `requirements.txt` güncel mi?
- `fonts/` dizini repo'da mı?
- Windows runner'da çalıştığından emin ol

### Problem: EXE çalışmıyor
**Çözüm:**
- Windows Defender uyarısını kontrol et
- `--console` modda hata mesajını oku
- Bağımlılıkların doğru paketlendiğini kontrol et

## 📧 Destek

Sorun yaşarsanız:
- GitHub Issues'a yazın
- Workflow log'larını inceleyin
- PyInstaller dokümantasyonunu okuyun

---

**Not:** İlk kez release yapıyorsanız, test için `v0.1.0-alpha` gibi bir pre-release tag'i kullanın.
