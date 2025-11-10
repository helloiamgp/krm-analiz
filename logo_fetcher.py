#!/usr/bin/env python3
"""
Banka Logo Çekme Aracı
Excel dosyasındaki bankalar için logo çeker ve kaydeder

Kullanım:
    python logo_fetcher.py
    python logo_fetcher.py --excel bankalar.xlsx --output logos/
"""

import openpyxl
import requests
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import time
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich.panel import Panel
from rich.table import Table
import re

console = Console()

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
    """
    Domain adını temizle (www. kaldır, geçersizleri düzelt).

    Args:
        domain: Ham domain adı

    Returns:
        Temizlenmiş domain
    """
    if not domain or domain == 'http:':
        return None

    # www. prefix'ini kaldır
    domain = domain.replace('www.', '')

    # Temizle
    domain = domain.strip().lower()

    return domain if domain else None

def sanitize_filename(name: str) -> str:
    """
    Dosya adını güvenli hale getir.

    Args:
        name: Ham dosya adı

    Returns:
        Güvenli dosya adı
    """
    # Türkçe karakterleri değiştir
    replacements = {
        'ı': 'i', 'İ': 'i', 'ş': 's', 'Ş': 's',
        'ğ': 'g', 'Ğ': 'g', 'ü': 'u', 'Ü': 'u',
        'ö': 'o', 'Ö': 'o', 'ç': 'c', 'Ç': 'c'
    }

    for old, new in replacements.items():
        name = name.replace(old, new)

    # Sadece alfanumerik ve - _ karakterleri bırak
    name = re.sub(r'[^a-zA-Z0-9\-_]', '_', name)

    # Çoklu alt çizgileri tek yap
    name = re.sub(r'_+', '_', name)

    # Başında ve sonundaki _ karakterlerini kaldır
    name = name.strip('_')

    return name.lower()

def fetch_logo(domain: str, bank_name: str, output_dir: Path) -> Optional[Path]:
    """
    Bir banka için logo çek ve kaydet.

    Args:
        domain: Banka domain adı
        bank_name: Banka adı (dosya adı için)
        output_dir: Logoların kaydedileceği dizin

    Returns:
        Kaydedilen dosyanın Path'i veya None
    """
    clean_domain_name = clean_domain(domain)
    if not clean_domain_name:
        return None

    # Dosya adını oluştur
    safe_name = sanitize_filename(bank_name)

    # Deneyeceğimiz domainler (fallback ile)
    domains_to_try = [clean_domain_name]

    # Eğer .com.tr ise, .com'u da dene
    if clean_domain_name.endswith('.com.tr'):
        global_domain = clean_domain_name.replace('.com.tr', '.com')
        domains_to_try.append(global_domain)

    # Her domain için tüm kaynakları dene
    for try_domain in domains_to_try:
        for source in LOGO_SOURCES:
            try:
                url = source['url_template'].format(domain=try_domain)

            # HTTP isteği yap
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }

                response = requests.get(
                    url,
                    timeout=source['timeout'],
                    headers=headers,
                    allow_redirects=True
                )

                # Başarılı mı?
                if response.status_code == 200 and len(response.content) > 100:  # En az 100 byte olmalı
                    # Content-Type'dan uzantıyı belirle
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
                        # İçerik başlangıcına bakarak tahmin et
                        if response.content.startswith(b'\x89PNG'):
                            ext = 'png'
                        elif response.content.startswith(b'\xff\xd8\xff'):
                            ext = 'jpg'
                        elif b'<svg' in response.content[:100]:
                            ext = 'svg'
                        else:
                            ext = 'png'  # Default

                    # Dosya yolunu oluştur
                    file_path = output_dir / f"{safe_name}.{ext}"

                    # Kaydet
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

                    return file_path

            except requests.exceptions.Timeout:
                continue  # Sonraki kaynağı dene
            except requests.exceptions.RequestException:
                continue  # Sonraki kaynağı dene
            except Exception:
                continue  # Sonraki kaynağı dene

    return None

def read_banks_from_excel(excel_path: Path) -> List[Dict[str, str]]:
    """
    Excel dosyasından banka listesini oku.

    Args:
        excel_path: Excel dosyasının path'i

    Returns:
        Banka bilgilerini içeren dict listesi
    """
    wb = openpyxl.load_workbook(excel_path)
    ws = wb.active

    banks = []

    for row in ws.iter_rows(min_row=2, values_only=True):
        banka_adi = row[0]
        web_adresi = row[6]

        # Kategorileri ve boşları atla
        if not banka_adi or not web_adresi:
            continue

        # Sadece gerçek bankaları al (kategori başlıklarını atla)
        if banka_adi.strip().startswith(' '):
            continue

        # Case-insensitive: bank/banka kelimesi içermeli
        banka_lower = str(banka_adi).lower()
        if 'bank' not in banka_lower and 'banka' not in banka_lower:
            continue

        # Domain çıkar
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

def fetch_all_logos(excel_path: Path, output_dir: Path) -> Tuple[int, int, List[str]]:
    """
    Tüm bankaların logolarını çek.

    Args:
        excel_path: Excel dosyasının path'i
        output_dir: Logoların kaydedileceği dizin

    Returns:
        (başarılı_sayısı, toplam_sayı, başarısız_bankalar) tuple'ı
    """
    # Output dizinini oluştur
    output_dir.mkdir(parents=True, exist_ok=True)

    # Bankaları oku
    console.print(f"[cyan]📊 Excel dosyası okunuyor:[/cyan] {excel_path.name}")
    banks = read_banks_from_excel(excel_path)

    if not banks:
        console.print("[red]❌ Hiç banka bulunamadı![/red]")
        return 0, 0, []

    console.print(f"[green]✓ {len(banks)} banka bulundu[/green]\n")

    # Logo çekme işlemi
    success_count = 0
    failed_banks = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green"),
        TaskProgressColumn(),
        console=console
    ) as progress:

        task = progress.add_task(
            "[cyan]Logolar çekiliyor...",
            total=len(banks)
        )

        for bank in banks:
            progress.update(task, description=f"[cyan]{bank['ad'][:40]}...")

            logo_path = fetch_logo(bank['domain'], bank['ad'], output_dir)

            if logo_path:
                success_count += 1
                progress.console.print(f"  [green]✓[/green] {bank['ad'][:50]} → {logo_path.name}")
            else:
                failed_banks.append(bank['ad'])
                progress.console.print(f"  [red]✗[/red] {bank['ad'][:50]} (logo bulunamadı)")

            progress.update(task, advance=1)

            # Rate limiting (nazik olalım)
            time.sleep(0.5)

    return success_count, len(banks), failed_banks

def main():
    """Ana fonksiyon."""
    console.print(Panel.fit(
        "[bold cyan]🏦 Banka Logo Çekme Aracı[/bold cyan]\n"
        "[dim]Excel'deki bankalar için logo çeker ve kaydeder[/dim]",
        border_style="cyan"
    ))

    # Varsayılan yollar
    excel_path = Path("2025-11-09_bankalar_listesi.xlsx")
    output_dir = Path("logos")

    # Excel dosyası var mı kontrol et
    if not excel_path.exists():
        console.print(f"[red]❌ Excel dosyası bulunamadı:[/red] {excel_path}")
        console.print("[yellow]Lütfen '2025-11-09_bankalar_listesi.xlsx' dosyasını bu dizine yerleştirin[/yellow]")
        return

    console.print(f"[cyan]📁 Output dizini:[/cyan] {output_dir.absolute()}\n")

    # Logoları çek
    success, total, failed = fetch_all_logos(excel_path, output_dir)

    # Özet
    console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
    console.print(f"[bold]📊 ÖZET[/bold]")
    console.print(f"[bold cyan]{'='*60}[/bold cyan]\n")

    console.print(f"Toplam banka: [cyan]{total}[/cyan]")
    console.print(f"Başarılı: [green]{success}[/green] ({success/total*100:.1f}%)")
    console.print(f"Başarısız: [red]{len(failed)}[/red] ({len(failed)/total*100:.1f}%)")

    if failed:
        console.print(f"\n[bold yellow]⚠️  Logo Bulunamayan Bankalar:[/bold yellow]")
        for bank_name in failed:
            console.print(f"  • {bank_name}")

    console.print(f"\n[green]✓ Logolar '{output_dir}/' dizinine kaydedildi[/green]")

    # Özet tablo
    if success > 0:
        console.print(f"\n[bold]Kaydedilen dosyalar:[/bold]")
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Dosya Adı", style="green")
        table.add_column("Boyut", justify="right")

        for logo_file in sorted(output_dir.glob("*")):
            if logo_file.is_file():
                size_kb = logo_file.stat().st_size / 1024
                table.add_row(logo_file.name, f"{size_kb:.1f} KB")

        console.print(table)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  İşlem kullanıcı tarafından iptal edildi[/yellow]")
    except Exception as e:
        console.print(f"\n[bold red]HATA:[/bold red] {str(e)}")
        import traceback
        console.print(traceback.format_exc())
