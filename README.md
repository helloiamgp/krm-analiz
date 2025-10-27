# KRM Rapor Analiz Aracı

Türkiye Bankalar Birliği (TBB) KRM raporlarını otomatik olarak analiz eden, limit aşımlarını tespit eden ve profesyonel PDF raporları oluşturan Python aracı.

## 🎯 Özellikler

- ✅ **PDF Parsing**: KRM PDF raporlarından limit ve risk bilgilerini otomatik çıkarma
- 🔍 **Anomali Tespiti**: 6 farklı risk senaryosunu otomatik tespit eder
  - Nakdi limit aşımı (WARNING/CRITICAL)
  - Gayrinakdi limit aşımı (WARNING/CRITICAL)
  - Limitsiz kullanım (CRITICAL)
  - Gecikme tespiti (30+ gün CRITICAL)
  - Toplam limit aşımı (CRITICAL)
  - Yüksek kullanım (>95% WARNING)
- 💤 **Pasif Kaynak Tespiti**: 180 günden eski revize tarihi + sıfır limit/risk kontrolü
- 📊 **Profesyonel PDF Raporları**: Renkli tablolar, severity göstergeleri, özet istatistikler
- 🎨 **Renkli Terminal Çıktısı**: Rich kütüphanesi ile modern CLI deneyimi
- 🚀 **Batch Processing**: Dizindeki tüm PDF'leri toplu analiz

## 📋 Gereksinimler

```bash
pip install pdfplumber reportlab rich
```

## 🚀 Kullanım

### Tek PDF Analizi
```bash
python krm.py rapor.pdf
```

### Toplu Analiz (Dizindeki Tüm PDF'ler)
```bash
python krm.py
```

## 📂 Çıktı Yapısı

```
KRM/
├── krm.py              # Ana program
├── *.pdf               # Girdi PDF dosyaları
└── output/             # Otomatik oluşturulur
    └── *.pdf           # Analiz raporları
```

## 🔧 Teknik Detaylar

### Kod Kalitesi
- ✅ **Type Hints**: Tüm fonksiyonlarda tam type annotation
- ✅ **Google Style Docstrings**: Profesyonel dokümantasyon
- ✅ **DRY Prensibi**: Helper fonksiyonlarla kod tekrarı minimizasyonu
- ✅ **Constants**: Magic number'lar yerine anlamlı sabitler
- ✅ **Error Handling**: Robust exception yönetimi

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
```

## 📊 Rapor İçeriği

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
   - Tüm limit ve risk verileri
   - Kullanım oranları
   - Zebra stripe formatı

## 🏦 GRC Sistemi Entegrasyonu

Bu araç Türk bankacılık sektörü için geliştirilmiş **GRC (Governance, Risk, Compliance)** sistemlerine entegre edilebilir:

- **BDDK** mevzuat uyumluluğu
- **TBB Risk Merkezi** veri analizi
- **KVKK** veri güvenliği gereksinimleri
- **ISO 27001** bilgi güvenliği standartları

### API Entegrasyon Örneği
```python
# Next.js API Route örneği
import { exec } from 'child_process';

export async function POST(req) {
  const { pdfPath } = await req.json();

  const { stdout } = await execAsync(`python3 krm.py ${pdfPath}`);

  // Output PDF'i Supabase'e yükle
  const { data } = await supabase.storage
    .from('krm-reports')
    .upload(`analysis/${Date.now()}.pdf`, outputPdf);

  return Response.json({ reportUrl: data.path });
}
```

## 📝 Lisans

MIT License

## 👤 Yazar

**helloiamgp**

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır. Büyük değişiklikler için lütfen önce bir issue açarak neyi değiştirmek istediğinizi tartışın.

## 📧 İletişim

Sorularınız için GitHub Issues kullanabilirsiniz.

---

**Not**: Bu araç TBB KRM PDF raporlarının belirli bir formatına göre tasarlanmıştır. Rapor formatı değişirse kod güncellemesi gerekebilir.
