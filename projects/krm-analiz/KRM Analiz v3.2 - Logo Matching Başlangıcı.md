# KRM Analiz v3.2 - Logo Matching Başlangıcı

## 🎯 Proje Özeti

KRM Analiz projesine logo matching özelliği eklendi. Bu özellik, Excel dosyasındaki bankaların logolarını çeker ve gelecekte KRM ve Findeks raporlarındaki banka logolarıyla eşleştirme yapmak için hazırlık oluşturur.

## ✅ Tamamlanan İşlemler

### 1. Excel Dosyası Analizi
- **Dosya**: `2025-11-09_bankalar_listesi.xlsx`
- **İçerik**: 47 banka bilgisi (isim, adres, web sitesi, vb.)
- **Kolonlar**: Banka Adı, Adres, Y.K. Başkanı, Genel Müdür, Telefon, Fax, Web Adresi, KEP Adresleri, Eft, Swift

### 2. Logo Çekme Fonksiyonu
İki versiyon oluşturuldu:

#### `logo_fetcher.py` (Rich UI ile)
- Gelişmiş progress bar
- Renkli konsol çıktısı
- Detaylı tablo raporları
- **Gereksinim**: `pip install rich`

#### `logo_fetcher_simple.py` (Bağımsız)
- Dış bağımlılık yok
- Basit konsol çıktısı
- Tüm özellikler çalışıyor

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

#### Başarı Oranı: **%95.7** (45/47 banka)

✅ **Başarılı**: 45 banka logosu indirildi
- Dosya formatları: PNG (çoğunluk), ICO (1 adet)
- Ortalama boyut: 5-15 KB
- Toplam: ~300 KB

❌ **Başarısız**: 2 banka
- Turkish Bank A.Ş. (turkishbank.com.tr - site erişilemez)
- Deutsche Bank A.Ş. (db.com.tr - özel domain)

#### İndirilen Logolar
Logolar `logos/` dizinine kaydedildi:
```
logos/
├── ziraat_bankasi_a_s.png (10.5 KB)
├── halkbank_a_s.png (6.6 KB)
├── vakifbank_t_a_o.png (4.6 KB)
├── akbank_t_a_s.png (12.3 KB)
├── garanti_bbva_a_s.png (9.4 KB)
└── ... (40 more)
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
- `Garanti BBVA` → `garanti_bbva.png`

### Rate Limiting
Her logo çekme isteği arasında 0.5 saniye bekleme yapılır (sunuculara nazik davranmak için).

### Hata Yönetimi
- Timeout: Her kaynak için 5-10 saniye
- Retry: 3 farklı kaynak otomatik denenir
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

## 🐛 Bilinen Sorunlar

1. **Turkish Bank ve Deutsche Bank logoları bulunamadı**
   - Çözüm: Manuel olarak indirilip `logos/` klasörüne eklenebilir

2. **Bazı logolar düşük çözünürlükte (Favicon fallback)**
   - Çözüm: Manuel yüksek çözünürlük logo ekleme

3. **SSL/TLS uyarısı (LibreSSL)**
   - Fonksiyonellik etkilenmez, sadece warning

## 📚 Bağımlılıklar

### Mevcut
- `openpyxl`: Excel okuma
- `requests`: HTTP istekleri
- `pathlib`: Dosya yönetimi

### Gelecek (Logo Matching için)
- `opencv-python`: Görsel işleme
- `pillow`: Image manipulation
- `tensorflow/pytorch`: Deep learning (opsiyonel)
- `numpy`: Array işlemleri

## 🎓 Öğrenilenler

1. **Multi-source fallback pattern**: Bir kaynak çalışmazsa diğerini dene
2. **Rate limiting**: API'lara nazik davran
3. **Content validation**: Header + Binary signature kombinasyonu
4. **Filename sanitization**: Cross-platform güvenli dosya adları
5. **Progress feedback**: Kullanıcı deneyimi için önemli

## 📝 Notlar

- Logo database'i düzenli güncellenmeli (yeni bankalar, logo değişiklikleri)
- OCR + Logo matching kombinasyonu en yüksek doğruluğu verecek
- Logo boyutu 128x128 veya 256x256 standardize edilebilir
- Database için SQLite yerine basit JSON da yeterli olabilir

---

**Son Güncelleme**: 10 Kasım 2025
**Versiyon**: 3.2
**Durum**: Logo çekme tamamlandı, matching planlanıyor
