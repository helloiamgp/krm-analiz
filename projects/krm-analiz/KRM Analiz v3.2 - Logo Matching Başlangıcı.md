# KRM Analiz v3.2 - Logo Matching Başlangıcı

## 🎯 Proje Özeti

KRM Analiz projesine logo matching özelliği eklendi. Bu özellik, Excel dosyasındaki **56 bankanın tamamının** logolarını çeker ve gelecekte KRM ve Findeks raporlarındaki banka logolarıyla eşleştirme yapmak için hazırlık oluşturur.

## ✅ Tamamlanan İşlemler

### 1. Excel Dosyası Analizi
- **Dosya**: `2025-11-09_bankalar_listesi.xlsx`
- **İçerik**: **56 banka bilgisi** (isim, adres, web sitesi, vb.)
- **Kolonlar**: Banka Adı, Adres, Y.K. Başkanı, Genel Müdür, Telefon, Fax, Web Adresi, KEP Adresleri, Eft, Swift

### 2. Logo Çekme Fonksiyonu
İki versiyon oluşturuldu:

#### `logo_fetcher.py` (Rich UI ile)
- Gelişmiş progress bar
- Renkli konsol çıktısı
- Detaylı tablo raporları
- **Gereksinim**: `pip install rich`

#### `logo_fetcher_simple.py` (Bağımsız) ⭐ ÖNERİLEN
- Dış bağımlılık yok
- Basit konsol çıktısı
- Tüm özellikler çalışıyor
- Case-insensitive banka kontrolü
- Global domain fallback mekanizması

### 3. Logo Kaynaları
Script, 3 farklı kaynaktan logo çekmeyi dener (sırayla):

1. **Clearbit Logo API**: `https://logo.clearbit.com/{domain}`
   - Yüksek kalite
   - Ücretsiz
   - Çoğu büyük şirket için çalışır

2. **Google Favicon API**: `https://www.google.com/s2/favicons?domain={domain}&sz=256`
   - 256x256 boyutunda
   - Güvenilir
   - Fallback seçeneği

3. **Direct Favicon**: `https://{domain}/favicon.ico`
   - Doğrudan site favicon'u
   - Son çare

### 4. Sonuçlar

#### Başarı Oranı: **%100** 🎉 (56/56 banka)

✅ **TÜMÜ BAŞARILI**: 56 banka logosu indirildi
- Dosya formatları: PNG (çoğunluk), ICO (1 adet)
- Ortalama boyut: 5-15 KB
- Toplam: ~500 KB

#### İndirilen Logolar
Logolar `logos/` dizinine kaydedildi:
```
logos/
├── akbank_t_a_s.png (3.7 KB)
├── ziraat_bankasi_a_s.png (10.5 KB)
├── halkbank_a_s.png (6.6 KB)
├── vakifbank_t_a_o.png (4.6 KB)
├── garanti_bbva_a_s.png (9.4 KB)
├── denizbank_a_s.png (4.2 KB)
├── rabobank_a_s.png (13.5 KB)
└── ... (49 more)
```

## 🚀 Kullanım

### Basit Versiyon (Önerilen)
```bash
python logo_fetcher_simple.py
```

### Rich UI Versiyonu
```bash
# Önce kurulum
pip install rich

# Çalıştır
python logo_fetcher.py
```

## 🔧 Teknik Detaylar

### Dosya Adı Güvenliği
Türkçe karakterler otomatik olarak temizlenir:
- `ı, İ → i`
- `ş, Ş → s`
- `ğ, Ğ → g`
- `ü, Ü → u`
- `ö, Ö → o`
- `ç, Ç → c`

Özel karakterler `_` ile değiştirilir.

**Örnek**:
- `Türkiye İş Bankası A.Ş.` → `turkiye_is_bankasi_a_s.png`
- `Garanti BBVA` → `turkiye_garanti_bankasi_a_s.png`

### Case-Insensitive Banka Kontrolü (v3.2.1)
Script artık büyük/küçük harf duyarsız:
```python
# Case-insensitive: bank/banka kelimesi içermeli
banka_lower = str(banka_adi).lower()
if 'bank' not in banka_lower and 'banka' not in banka_lower:
    continue
```

**Sonuç**: Akbank, Anadolubank, Fibabanka, Şekerbank gibi bankalar artık yakalanıyor!

### Global Domain Fallback (v3.2.2) 🎯
Türkiye domainleri (.com.tr) başarısız olursa global (.com) denenir:

```python
domains_to_try = [clean_domain_name]

# Eğer .com.tr ise, .com'u da dene
if clean_domain_name.endswith('.com.tr'):
    global_domain = clean_domain_name.replace('.com.tr', '.com')
    domains_to_try.append(global_domain)
```

**Sonuç**:
- Turkish Bank: `turkishbank.com.tr` ❌ → `turkishbank.com` ✅
- Deutsche Bank: `db.com.tr` ❌ → `db.com` ✅ (Google Favicon)
- Rabobank: `rabobank.com.tr` ❌ → `rabobank.com` ✅ (Clearbit, 13.5 KB)

### Rate Limiting
Her logo çekme isteği arasında 0.5 saniye bekleme yapılır (sunuculara nazik davranmak için).

### Hata Yönetimi
- Timeout: Her kaynak için 5-10 saniye
- Retry: 3 farklı kaynak otomatik denenir
- Fallback: .com.tr → .com domain değişimi
- Validation: En az 100 byte kontrolü (boş/hata sayfalarını engeller)

## 📊 Veri Yapısı

### Excel'den Okunan Banka Formatı
```python
{
    'ad': 'Türkiye Cumhuriyeti Ziraat Bankası A.Ş.',
    'web': 'http://www.ziraatbank.com.tr',
    'domain': 'www.ziraatbank.com.tr'
}
```

### Kaydedilen Logo Formatı
```
{filename}.{ext}
```
- **filename**: Sanitize edilmiş banka adı
- **ext**: png, jpg, svg, ico, webp (otomatik tespit)

## 🎨 Logo Formatları

Script otomatik olarak format tespiti yapar:
- **Content-Type** header kontrolü
- Binary signature kontrolü (magic bytes):
  - PNG: `\x89PNG`
  - JPEG: `\xff\xd8\xff`
  - SVG: `<svg`

## 📈 Versiyon Geçmişi

### v3.2 - İlk Durum (10 Kas 2025)
- 47 banka bulundu
- 45 logo çekildi (%95.7)
- 2 başarısız (Turkish Bank, Deutsche Bank)

### v3.2.1 - Case-Insensitive Fix
- **56 banka** bulundu (+9 banka)
  - Akbank, Anadolubank, Fibabanka, Şekerbank
  - Alternatifbank, Citibank, Denizbank
  - Türk Eximbank, Rabobank
- 53 logo çekildi (%94.6)
- 3 başarısız (Turkish Bank, Deutsche Bank, Rabobank)

### v3.2.2 - Global Domain Fallback ✅
- **56 banka** bulundu
- **56 logo çekildi** (%100) 🎉
- **0 başarısız**
- Tüm Türk bankaları için global fallback

## 🔮 Gelecek Adımlar

### 1. Logo Matching (Planlanıyor)
KRM/Findeks raporlarındaki logolarla eşleştirme:

**Yaklaşım 1: Template Matching**
```python
import cv2

def match_logo(pdf_logo, bank_logo_db):
    """
    OpenCV template matching ile logo tespiti
    """
    # PDF'den logo extract et
    # Database logoları ile karşılaştır
    # En yüksek benzerlik skorunu döndür
```

**Yaklaşım 2: Feature Matching**
```python
import cv2

def feature_match_logos(logo1, logo2):
    """
    SIFT/ORB feature matching
    """
    # Feature extraction
    # Feature matching
    # Similarity score
```

**Yaklaşım 3: Deep Learning**
```python
from tensorflow.keras.applications import ResNet50

def deep_logo_match(logo1, logo2):
    """
    Pre-trained CNN ile feature extraction
    """
    # ResNet50 feature extractor
    # Cosine similarity
```

### 2. PDF'den Logo Çıkarma
```python
def extract_logos_from_pdf(pdf_path):
    """
    KRM/Findeks PDF'lerinden logo görsellerini çıkar
    """
    import fitz  # PyMuPDF

    pdf = fitz.open(pdf_path)
    logos = []

    for page in pdf:
        images = page.get_images()
        for img in images:
            # Logo boyutu filtreleme
            # ROI (Region of Interest) detection
            logos.append(extract_image(img))

    return logos
```

### 3. Otomatik Banka Eşleştirme
Mevcut `clean_bank_name_ocr()` fonksiyonu ile entegrasyon:
```python
def match_bank_to_logo(ocr_text, logo_database):
    """
    OCR metni + logo matching kombinasyonu
    """
    # 1. OCR ile banka adı temizle
    bank_name = clean_bank_name_ocr(ocr_text)

    # 2. Logo match yap
    logo_score = match_logo(extracted_logo, bank_name)

    # 3. Kombine skor
    confidence = combine_scores(text_score, logo_score)

    return bank_name, confidence
```

## 📋 TODO

- [ ] OpenCV kurulumu ve test
- [ ] PDF'den logo extraction fonksiyonu
- [ ] Logo matching algoritması
- [ ] Confidence score sistemi
- [ ] Logo database yönetimi (SQLite?)
- [ ] Logo güncelleme otomasyonu (quarterly refresh)
- [ ] Benchmark: Template vs Feature vs Deep Learning
- [x] ~~Global domain fallback~~ ✅
- [x] ~~Case-insensitive banka kontrolü~~ ✅
- [x] ~~56 bankanın tamamı~~ ✅

## 📚 Bağımlılıklar

### Mevcut
- `openpyxl`: Excel okuma
- `requests`: HTTP istekleri
- `pathlib`: Dosya yönetimi
- `rich`: UI (opsiyonel, sadece logo_fetcher.py)

### Gelecek (Logo Matching için)
- `opencv-python`: Görsel işleme
- `pillow`: Image manipulation
- `tensorflow/pytorch`: Deep learning (opsiyonel)
- `numpy`: Array işlemleri

## 🎓 Öğrenilenler

1. **Multi-source fallback pattern**: Bir kaynak çalışmazsa diğerini dene
2. **Global domain fallback**: .com.tr → .com dönüşümü kritik
3. **Rate limiting**: API'lara nazik davran
4. **Content validation**: Header + Binary signature kombinasyonu
5. **Filename sanitization**: Cross-platform güvenli dosya adları
6. **Progress feedback**: Kullanıcı deneyimi için önemli
7. **Case-insensitive search**: Türkçe banka isimleri için gerekli

## 📝 Notlar

- Logo database'i düzenli güncellenmeli (yeni bankalar, logo değişiklikleri)
- OCR + Logo matching kombinasyonu en yüksek doğruluğu verecek
- Logo boyutu 128x128 veya 256x256 standardize edilebilir
- Database için SQLite yerine basit JSON da yeterli olabilir
- Global fallback mekanizması diğer ülkeler için de genişletilebilir (.co.uk, .de, vb.)

## 🐛 Bilinen Sorunlar

~~1. **Turkish Bank, Deutsche Bank ve Rabobank logoları bulunamıyor**~~
   - ✅ **ÇÖZÜLDÜ**: Global domain fallback ile %100 başarı

~~2. **Akbank, Anadolubank gibi küçük 'bank' yazılan bankalar atlanıyor**~~
   - ✅ **ÇÖZÜLDÜ**: Case-insensitive kontrol eklendi

3. **SSL/TLS uyarısı (LibreSSL)**
   - Fonksiyonellik etkilenmez, sadece warning

## 🔗 Git Commits

1. **88a735e** - "feat: Banka logo çekme sistemi eklendi (v3.2)"
   - İlk logo çekme sistemi
   - 3 kaynak (Clearbit, Google, Direct)
   - 47 banka, 45 logo (%95.7)

2. **a782fdc** - "fix: Case-insensitive banka kontrolü - 9 eksik banka eklendi"
   - Case-insensitive search
   - 56 banka, 53 logo (%94.6)
   - +9 yeni banka (Akbank, Anadolubank, vb.)

3. **748b028** - "feat: Global domain fallback - %100 başarı oranı! 🎉"
   - .com.tr → .com fallback
   - 56 banka, 56 logo (%100) ✅
   - Turkish Bank, Deutsche Bank, Rabobank çözüldü

---

**Son Güncelleme**: 10 Kasım 2025
**Versiyon**: 3.2.2
**Durum**: ✅ Tamamlandı - %100 başarı
**Sonraki**: Logo matching algoritması
