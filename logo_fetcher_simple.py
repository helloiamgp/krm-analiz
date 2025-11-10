#!/usr/bin/env python3
"""
Banka Logo Çekme Aracı (Basit Versiyon)
Excel dosyasındaki bankalar için logo çeker ve kaydeder

Kullanım:
    python logo_fetcher_simple.py
"""

import openpyxl
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import time
import re

# Logo kaynakları (sırayla denenecek)
LOGO_SOURCES = [
    {
        'name': 'Clearbit',
        'url_template': 'https://logo.clearbit.com/{domain}',
        'timeout': 10
    },
    {
        'name': 'Google Favicon',
        'url_template': 'https://www.google.com/s2/favicons?domain={domain}&sz=256',
        'timeout': 10
    },
    {
        'name': 'Direct Favicon',
        'url_template': 'https://{domain}/favicon.ico',
        'timeout': 5
    }
]

def clean_domain(domain: str) -> str:
    """Domain adını temizle."""
    if not domain or domain == 'http:':
        return None
    domain = domain.replace('www.', '').strip().lower()
    return domain if domain else None

def sanitize_filename(name: str) -> str:
    """Dosya adını güvenli hale getir."""
    replacements = {
        'ı': 'i', 'İ': 'i', 'ş': 's', 'Ş': 's',
        'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
        'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }
    for old, new in replacements.items():
        name = name.replace(old, new)
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)
    name = re.sub(r'_+', '_', name)
    return name.strip('_').lower()

def fetch_logo(domain: str, bank_name: str, output_dir: Path) -> Optional[Path]:
    """Bir banka için logo çek ve kaydet."""
    clean_domain_name = clean_domain(domain)
    if not clean_domain_name:
        return None

    safe_name = sanitize_filename(bank_name)

    for source in LOGO_SOURCES:
        try:
            url = source['url_template'].format(domain=clean_domain_name)
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=source['timeout'], headers=headers, allow_redirects=True)

            if response.status_code == 200 and len(response.content) > 100:
                content_type = response.headers.get('Content-Type', '').lower()

                if 'png' in content_type:
                    ext = 'png'
                elif 'jpeg' in content_type or 'jpg' in content_type:
                    ext = 'jpg'
                elif 'svg' in content_type:
                    ext = 'svg'
                elif 'webp' in content_type:
                    ext = 'webp'
                elif 'ico' in content_type or 'icon' in content_type:
                    ext = 'ico'
                else:
                    if response.content.startswith(b'\x89PNG'):
                        ext = 'png'
                    elif response.content.startswith(b'\xff\xd8\xff'):
                        ext = 'jpg'
                    elif b'<svg' in response.content[:100]:
                        ext = 'svg'
                    else:
                        ext = 'png'

                file_path = output_dir / f"{safe_name}.{ext}"
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                return file_path
        except:
            continue
    return None

def read_banks_from_excel(excel_path: Path) -> List[Dict[str, str]]:
    """Excel dosyasından banka listesini oku."""
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active
    banks = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        banka_adi = row[0]
        web_adresi = row[6]

        if not banka_adi or not web_adresi:
            continue

        # Kategori başlıklarını atla
        if banka_adi.strip().startswith(' '):
            continue

        # Case-insensitive: bank/banka kelimesi içermeli
        banka_lower = str(banka_adi).lower()
        if 'bank' not in banka_lower and 'banka' not in banka_lower:
            continue

        try:
            if not web_adresi or web_adresi.strip() == 'http://':
                continue

            domain = urlparse(web_adresi).netloc or urlparse('http://' + web_adresi.strip()).netloc

            if domain and domain != 'http:':
                banks.append({
                    'ad': banka_adi.strip(),
                    'web': web_adresi.strip(),
                    'domain': domain
                })
        except:
            pass

    return banks

def main():
    """Ana fonksiyon."""
    print("=" * 60)
    print("🏦 BANKA LOGO ÇEKME ARACI")
    print("=" * 60)
    print()

    excel_path = Path("2025-11-09_bankalar_listesi.xlsx")
    output_dir = Path("logos")

    if not excel_path.exists():
        print(f"❌ HATA: Excel dosyası bulunamadı: {excel_path}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"📊 Excel dosyası okunuyor: {excel_path.name}")
    banks = read_banks_from_excel(excel_path)

    if not banks:
        print("❌ Hiç banka bulunamadı!")
        return

    print(f"✓ {len(banks)} banka bulundu")
    print(f"📁 Output dizini: {output_dir.absolute()}")
    print()

    success_count = 0
    failed_banks = []

    print("Logolar çekiliyor...\n")

    for i, bank in enumerate(banks, 1):
        print(f"[{i}/{len(banks)}] {bank['ad'][:50]}...", end=' ')

        logo_path = fetch_logo(bank['domain'], bank['ad'], output_dir)

        if logo_path:
            success_count += 1
            print(f"✓ ({logo_path.name})")
        else:
            failed_banks.append(bank['ad'])
            print("✗ (logo bulunamadı)")

        time.sleep(0.5)

    print()
    print("=" * 60)
    print("📊 ÖZET")
    print("=" * 60)
    print(f"Toplam banka: {len(banks)}")
    print(f"Başarılı: {success_count} ({success_count/len(banks)*100:.1f}%)")
    print(f"Başarısız: {len(failed_banks)} ({len(failed_banks)/len(banks)*100:.1f}%)")

    if failed_banks:
        print(f"\n⚠️  Logo Bulunamayan Bankalar:")
        for bank_name in failed_banks:
            print(f"  • {bank_name}")

    print(f"\n✓ Logolar '{output_dir}/' dizinine kaydedildi")

    # Kaydedilen dosyaları listele
    if success_count > 0:
        print("\nKaydedilen dosyalar:")
        for logo_file in sorted(output_dir.glob("*")):
            if logo_file.is_file():
                size_kb = logo_file.stat().st_size / 1024
                print(f"  • {logo_file.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️  İşlem kullanıcı tarafından iptal edildi")
    except Exception as e:
        print(f"\n❌ HATA: {str(e)}")
        import traceback
        traceback.print_exc()
