# KRM Rapor Analiz Aracı v3

Türkiye Bankalar Birliği (TBB) KRM raporlarını otomatik olarak analiz eden, Findeks raporlarıyla eşleştiren, limit aşımlarını tespit eden ve profesyonel PDF raporları oluşturan Python aracı.

## 🎯 Özellikler

### 📁 Klasör Bazlı Analiz
- ✅ **Alt Klasör Tarama**: Otomatik olarak tüm alt klasörleri tarar
- ✅ **Firma Bazlı Organizasyon**: Her firma/dönem için ayrı klasör
- ✅ **Otomatik Findeks Eşleştirme**: Her klasördeki KRM ile Findeks raporu eşleştirilir
- ✅ **Klasör Bazlı Raporlama**: Her klasörün kendi output/ dizini

### 🎨 İnteraktif CLI Arayüzü (v3.1 YENİ!)
- ✅ **Progress Bars**: Real-time ilerleme göstergeleri
- ✅ **Spinner Animasyonları**: İşlem sırasında görsel feedback
- ✅ **Kalan Süre Tahmini**: Ne kadar bekleneceği bilgisi
- ✅ **Klasör/PDF Seviyesinde Tracking**: Her adım takip edilir
- ✅ **Tree View**: Klasör yapısını görsel ağaç formatında gösterir
- ✅ **Live Status**: İlk PDF için adım adım parsing gösterimi

### 🔍 Analiz Özellikleri
- ✅ **PDF Parsing**: KRM PDF raporlarından limit ve risk bilgilerini otomatik çıkarma
- ✅ **OCR Desteği**: Findeks raporlarından banka isimlerini okur (PyMuPDF + Tesseract)
- ✅ **Akıllı Eşleştirme**: KRM kaynakları ile Findeks kurumlarını %15 toleransla eşleştirir
- 🔍 **Anomali Tespiti**: 6 farklı risk senaryosunu otomatik tespit eder
- 🔒 **Güvenlik Kontrolleri**: PDF validation, path traversal koruması, dosya boyutu limiti
  - Nakdi limit aşımı (WARNING/CRITICAL)
  - Gayrinakdi limit aşımı (WARNING/CRITICAL)
  - Limitsiz kullanım (CRITICAL)
  - Gecikme tespiti (30+ gün CRITICAL)
  - Toplam limit aşımı (CRITICAL)
  - Yüksek kullanım (>95% WARNING)
- 💤 **Pasif Kaynak Tespiti**: 180 günden eski revize tarihi + sıfır limit/risk kontrolü

### 📊 Raporlama
- 📊 **Profesyonel PDF Raporları**: Renkli tablolar, severity göstergeleri, özet istatistikler
- 🎨 **Renkli Terminal Çıktısı**: Rich kütüphanesi ile modern CLI deneyimi
- 🚀 **Toplu İşlem**: Tüm klasörlerdeki tüm raporları tek seferde analiz eder

## 📋 Gereksinimler

```bash
pip install pdfplumber reportlab rich PyMuPDF pytesseract Pillow
```

**OCR için ek gereksinim (Findeks eşleştirme için):**
- **macOS**: `brew install tesseract`
- **Ubuntu**: `sudo apt-get install tesseract-ocr`
- **Windows**: [Tesseract Installer](https://github.com/UB-Mannheim/tesseract/wiki)

## 📂 Klasör Yapısı

### Önerilen Organizasyon

```
/Ana_Dizin/
  ├── krm.py              # Ana program
  ├── fonts/              # DejaVu Sans fontları
  │   ├── DejaVuSans.ttf
  │   └── DejaVuSans-Bold.ttf
  │
  ├── Firma_A/            # Firma klasörü
  │   ├── KRM_2024.pdf
  │   ├── Findeks_2024.pdf
  │   └── output/         # ← Otomatik oluşturulur
  │       └── KRM_2024.pdf
  │
  ├── Firma_B/
  │   ├── ABC_KRM.pdf
  │   ├── ABC_Findeks.pdf
  │   └── output/
  │       └── ABC_KRM.pdf
  │
  └── Firma_C/
      ├── XYZ_KRM.pdf     # Findeks yok, eşleştirme atlanır
      └── output/
          └── XYZ_KRM.pdf
```

### Klasör İsimlendirme

Klasör isimleri serbestçe verilebilir:
- `Firma_A`, `Firma_B` gibi jenerik isimler
- `2024_Ocak`, `2024_Subat` gibi dönem bazlı
- `Parafaktoring`, `GarantiBank` gibi firma adları
- `output`, `fonts`, `.git` gibi sistem klasörleri otomatik atlanır

### PDF İsimlendirme

Program otomatik algılar:
- **KRM Raporları**: İsimde `KRM` veya `krm` geçmeli
- **Findeks Raporları**: İsimde `Findeks` veya `findeks` geçmeli

## 🚀 Kurulum ve Kullanım

### Seçenek 1: Windows EXE Dosyası (ÖNERİLEN)

**⚡ Hızlı Başlangıç:**
1. [Releases](https://github.com/helloiamgp/krm-analiz/releases/latest) sayfasından **KRM-Analiz.exe** indirin
2. İstediğiniz klasöre kopyalayın
3. Alt klasörler oluşturup içlerine PDF'leri yerleştirin
4. **Çift tıklayın** → Tüm klasörler analiz edilir!

**Avantajlar:**
- ✅ Hiçbir kurulum gerektirmez
- ✅ Python bilgisi gerektirmez
- ✅ Çift tıklama ile çalışır
- ✅ Tesseract OCR dahil

### Seçenek 2: Python Script

**Kurulum (İlk Seferinde):**
```bash
# Temel bağımlılıklar
pip install -r requirements.txt

# OCR için Tesseract (opsiyonel, Findeks eşleştirme için)
# macOS
brew install tesseract

# Ubuntu/Debian
sudo apt-get install tesseract-ocr

# Windows
# https://github.com/UB-Mannheim/tesseract/wiki adresinden indirebilirsiniz
```

**Kullanım:**

```bash
# Tüm alt klasörleri analiz et
python3 krm.py

# Program otomatik olarak:
# 1. Alt klasörleri tarar
# 2. Her klasördeki KRM ve Findeks PDF'leri bulur
# 3. Eşleştirme yapar
# 4. Her klasöre output/ dizini oluşturur
# 5. Analiz raporlarını kaydeder
```

## 📊 Program Çıktısı

### Terminal Çıktısı

```
╔══════════════════════════════════════════════════════════╗
║     KRM Rapor Analiz Aracı v3.1                         ║
║     Klasör bazlı analiz, Findeks eşleştirmesi           ║
╚══════════════════════════════════════════════════════════╝

📂 Alt klasörler taranıyor: /Ana_Dizin

✓ Firma_A/
  KRM: 1 adet
    → PARAFİNANS_KRM.pdf
  Findeks: 1 adet
    → FindeksRapor.pdf

📂 Bulunan Klasörler
├── Firma_A/
│   ├── 📄 KRM Raporları
│   │   └── PARAFİNANS_KRM.pdf (2.3 MB)
│   ├── 📊 Findeks Raporları
│   │   └── FindeksRapor.pdf (1.8 MB)
│   └── 📁 output/ (oluşturulacak)
└── Firma_B/
    ├── 📄 KRM Raporları
    │   └── XYZ_KRM.pdf (1.9 MB)
    └── 📁 output/ (oluşturulacak)

════════════════════════════════════════════════════════════
Toplam 2 klasör işlenecek

⠋ 📂 Klasörler işleniyor... ████████████░░░░ 50% • 0:00:15
  ↳ PARAFİNANS_KRM.pdf... ████████████ 100%

┌─────────────────────────────────┐
│ 🔍 PARAFİNANS_KRM.pdf           │
├─────────────────────────────────┤
│ ✓ PDF Açılıyor                  │
│ ✓ Header Parsing                │
│ ⏳ Limit Tablosu                │
│ ○ Risk Tablosu                  │
│ ○ Pasif Kaynak                  │
│ ○ Anomali Taraması              │
└─────────────────────────────────┘

════════════════════════════════════════════════════════════
KLASÖR 1/2: Firma_A
════════════════════════════════════════════════════════════

🔗 Findeks: FindeksRapor.pdf
    ✓ PARAFİNANS_KRM.pdf
🔗 Findeks eşleştirmesi yapılıyor...
✓ 8 eşleştirme bulundu

📊 Firma_A - Özet:
  Toplam Kaynak: 12
  ✅ Aktif Kaynak: 10
  💤 Pasif Kaynak: 2
  Tespit Edilen Sorun: 3
  🔴 Kritik: 2
  🟡 Uyarı: 1

════════════════════════════════════════════════════════════
GENEL ÖZET - TÜM KLASÖRLER
════════════════════════════════════════════════════════════

İşlenen Klasör Sayısı: 2
Analiz Edilen Rapor: 2
Toplam Aktif Kaynak: 18
Toplam Pasif Kaynak: 4
Toplam Kritik Sorun: 4
Toplam Uyarı: 2

✓ Tüm PDF raporlar ilgili klasörlerdeki output/ dizinlerine kaydedildi
```

### PDF Rapor İçeriği

1. **Özet İstatistikler**
   - Toplam/Aktif/Pasif kaynak sayısı
   - Kritik sorun ve uyarı sayısı

2. **Pasif Kaynaklar Tablosu**
   - Son revize tarihleri
   - Grup ve toplam limitler
   - Pasif durum göstergesi

3. **Kritik Sorunlar** (Kırmızı arka plan)
   - Kaynak bazında detaylı açıklama
   - TL bazında aşım miktarları

4. **Uyarılar** (Sarı arka plan)
   - Potansiyel risk alanları
   - Kullanım yüzdeleri

5. **Detaylı Aktif Kaynak Bilgileri**
   - Findeks eşleştirme sonuçları (✅ YENİ!)
   - Tüm limit ve risk verileri
   - Kullanım oranları
   - Zebra stripe formatı

## 🔒 Güvenlik Özellikleri

### PDF Güvenlik Kontrolleri
```python
# Otomatik güvenlik kontrolleri:
✅ PDF magic number doğrulama (%PDF- header)
✅ Dosya boyutu limiti (max 100 MB, DOS koruması)
✅ Symlink dosyaları engelleme
✅ Bozuk/sahte PDF tespiti
✅ Boş veya geçersiz PDF kontrolü
✅ Aşırı büyük PDF kontrolü (max 1000 sayfa)
```

### Path Traversal Koruması
```python
# Tehlikeli path örnekleri - otomatik engellenir:
❌ ../../../etc/passwd
❌ /sistem/dosya.pdf
❌ Symlink manipülasyonu
❌ Network share yolları

✅ Sadece program dizini altındaki dosyalara erişim
✅ Tüm dosya yolları güvenlik kontrolünden geçer
```

### Güvenli Kullanım
- Program sadece kendi dizini ve alt klasörlerindeki dosyalara erişir
- Geçersiz PDF'ler otomatik atlanır ve uyarı verilir
- Tüm dosya işlemleri güvenlik kontrolünden geçer
- Şüpheli dosyalar detaylı hata mesajı ile reddedilir

## 🔧 Teknik Detaylar

### Kod Kalitesi
- ✅ **Type Hints**: Tüm fonksiyonlarda tam type annotation
- ✅ **Google Style Docstrings**: Profesyonel dokümantasyon
- ✅ **DRY Prensibi**: Helper fonksiyonlarla kod tekrarı minimizasyonu
- ✅ **Constants**: Magic number'lar yerine anlamlı sabitler
- ✅ **Error Handling**: Robust exception yönetimi
- ✅ **Tek Dosya**: Tüm modüller tek krm.py'de birleşik (PyInstaller uyumlu)

### Analiz Algoritması

#### Pasif Kaynak Kriterleri
```python
PASSIVE_SOURCE_CUTOFF_DAYS = 180

# Bir kaynak şu durumlarda pasif sayılır:
if revize_tarihi < (bugün - 180 gün) AND toplam_limit == 0 AND toplam_risk == 0:
    # Pasif kaynak
```

#### Risk Threshold'ları
```python
CRITICAL_DELAY_DAYS = 30           # 30+ gün gecikme = CRITICAL
HIGH_USAGE_THRESHOLD = 95.0        # %95+ kullanım = WARNING
CRITICAL_USAGE_THRESHOLD = 100.0   # %100+ kullanım = CRITICAL
FINDEKS_MATCH_THRESHOLD = 0.15     # %15 tolerans (eşleştirme için)
```

#### Findeks Eşleştirme Algoritması

```python
# 1. OCR ile banka isimlerini oku (PyMuPDF + Tesseract)
# 2. Her KRM kaynağı için skorlama yap:

score = 0.0
score += nakdi_limit_fark * 2.0      # Ağırlık: 2x
score += gayrinakdi_limit_fark * 1.5 # Ağırlık: 1.5x
score += nakdi_risk_fark * 2.0       # Ağırlık: 2x
score += gayrinakdi_risk_fark * 1.5  # Ağırlık: 1.5x
score += toplam_limit_fark * 1.0     # Ağırlık: 1x

# 3. Güven seviyesi belirle:
if score <= 0.05:  → HIGH confidence    (≤%5 fark)
if score <= 0.10:  → MEDIUM confidence  (%5-10 fark)
if score <= 0.15:  → LOW confidence     (%10-15 fark)
if score > 0.15:   → Eşleşme yok
```

## 🏦 GRC Sistemi Entegrasyonu

Bu araç Türk bankacılık sektörü için geliştirilmiş **GRC (Governance, Risk, Compliance)** sistemlerine entegre edilebilir:

- **BDDK** mevzuat uyumluluğu
- **TBB Risk Merkezi** veri analizi
- **KVKK** veri güvenliği gereksinimleri
- **ISO 27001** bilgi güvenliği standartları

### Next.js + Supabase API Entegrasyon Örneği

```typescript
// app/api/krm-analyze/route.ts
import { exec } from 'child_process';
import { promisify } from 'util';
import { createClient } from '@supabase/supabase-js';

const execAsync = promisify(exec);
const supabase = createClient(process.env.SUPABASE_URL!, process.env.SUPABASE_KEY!);

export async function POST(req: Request) {
  const { folderPath } = await req.json();

  // KRM analizi çalıştır
  const { stdout } = await execAsync(`python3 krm.py`, {
    cwd: folderPath
  });

  // Üretilen PDF'leri Supabase'e yükle
  const outputFiles = await fs.readdir(`${folderPath}/output`);

  for (const file of outputFiles) {
    const pdfBuffer = await fs.readFile(`${folderPath}/output/${file}`);

    await supabase.storage
      .from('krm-reports')
      .upload(`${Date.now()}_${file}`, pdfBuffer, {
        contentType: 'application/pdf'
      });
  }

  return Response.json({ success: true, fileCount: outputFiles.length });
}
```

## 🛠️ PyInstaller ile EXE Oluşturma

```bash
# Tek komut (fonts klasörünü dahil eder)
pyinstaller krm.spec

# Manuel oluşturma
pyinstaller --onefile --add-data "fonts:fonts" --name "KRM-Analiz" krm.py

# Çıktı: dist/KRM-Analiz.exe
```

## 📝 Lisans

MIT License

## 👤 Yazar

**helloiamgp**

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için lütfen önce bir issue açarak neyi değiştirmek istediğinizi tartışın.

## 🐛 Bilinen Sorunlar

- Findeks OCR başarısız olursa eşleştirme atlanır (hata vermez)
- Tesseract kurulu değilse Findeks eşleştirme yapılamaz
- KRM rapor formatı değişirse kod güncellemesi gerekir

## 📧 İletişim

Sorularınız için GitHub Issues kullanabilirsiniz.

---

## 🔄 Versiyon Geçmişi

### v3.1 (Kasım 2024)
- 🎨 İnteraktif progress bar'lar eklendi
- 🎨 Real-time ilerleme göstergeleri
- 🎨 Spinner animasyonları
- 🎨 Kalan süre tahmini
- 🎨 Tree View - klasör yapısını görsel ağaç formatında gösterir
- 🎨 Live Status - ilk PDF için adım adım parsing gösterimi
- 🔒 PDF güvenlik validation eklendi
- 🔒 Path traversal koruması
- 🔒 Dosya boyutu limiti (DOS koruması)
- 🔒 Symlink dosyaları engelleme
- 🔒 Bozuk/sahte PDF tespiti

### v3.0 (Kasım 2024)
- ✨ Klasör bazlı analiz sistemi
- ✨ Otomatik Findeks eşleştirme (OCR)
- ✨ Her klasör için ayrı output dizini
- ✨ Toplu işlem desteği

### v2.0 (Ekim 2024)
- ✨ Findeks rapor desteği eklendi
- ✨ OCR tabanlı banka ismi çıkarma
- ✨ Eşleştirme algoritması

### v1.0 (Ekim 2024)
- 🎉 İlk sürüm
- ✅ KRM PDF parsing
- ✅ Anomali tespiti
- ✅ PDF rapor üretimi

---

**Not**: Bu araç TBB KRM ve Findeks PDF raporlarının belirli formatlarına göre tasarlanmıştır. Rapor formatı değişirse kod güncellemesi gerekebilir.
