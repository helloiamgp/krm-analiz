#!/usr/bin/env python3
"""
KRM Rapor Analiz Aracı
PDF çıktı ile profesyonel raporlama

Gereksinimler:
    pip install pdfplumber reportlab PyMuPDF pytesseract Pillow rich

Kullanım:
    python krm.py                  # Dizindeki tüm PDF'leri analiz et
    python krm.py rapor.pdf        # Sadece belirtilen PDF'i analiz et
"""

import pdfplumber
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
from rich.tree import Tree
from rich.live import Live
from rich.layout import Layout

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table as RLTable, TableStyle, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Constants
PASSIVE_SOURCE_CUTOFF_DAYS = 180
HIGH_USAGE_THRESHOLD = 95.0
CRITICAL_USAGE_THRESHOLD = 100.0
CRITICAL_DELAY_DAYS = 30
FINDEKS_MATCH_THRESHOLD = 0.15  # %15 tolerans

console = Console()

# ========================================
# GÜVENLİK FONKSİYONLARI
# ========================================

def validate_pdf_file(file_path: Path, max_size_mb: int = 100) -> Tuple[bool, str]:
    """
    PDF dosyasını güvenlik kontrolünden geçir.

    Args:
        file_path: Kontrol edilecek PDF dosyası
        max_size_mb: Maksimum dosya boyutu (MB)

    Returns:
        (is_valid, error_message) tuple'ı

    Kontroller:
        - Dosya var mı?
        - Normal dosya mı? (symlink değil)
        - Boyut limiti aşılmış mı?
        - PDF uzantısı var mı?
        - PDF header'ı geçerli mi? (%PDF-)
        - pdfplumber ile açılabiliyor mu?
    """
    try:
        # 1. Dosya var mı?
        if not file_path.exists():
            return False, f"Dosya bulunamadı"

        # 2. Normal dosya mı? (symlink, directory değil)
        if not file_path.is_file():
            return False, f"Geçerli bir dosya değil"

        # 3. Symlink kontrolü
        if file_path.is_symlink():
            return False, f"Symlink dosyalar güvenlik nedeniyle desteklenmiyor"

        # 4. Boyut kontrolü (DOS ataklarına karşı)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"Dosya çok büyük ({file_size_mb:.1f} MB > {max_size_mb} MB)"

        # 5. Boş dosya kontrolü
        if file_size_mb < 0.001:  # 1 KB'den küçük
            return False, f"Dosya çok küçük veya boş"

        # 6. Uzantı kontrolü
        if file_path.suffix.lower() != '.pdf':
            return False, f"Sadece PDF dosyaları destekleniyor (.{file_path.suffix})"

        # 7. PDF header kontrolü (%PDF-1.x)
        try:
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if not header.startswith(b'%PDF-'):
                    return False, "Geçersiz PDF formatı (header kontrol)"
        except Exception as e:
            return False, f"Dosya okunamıyor: {e}"

        # 8. pdfplumber ile açılabilirlik testi
        try:
            with pdfplumber.open(file_path) as pdf:
                if len(pdf.pages) == 0:
                    return False, "PDF boş (sayfa yok)"

                # Aşırı fazla sayfa kontrolü (DOS)
                if len(pdf.pages) > 1000:
                    return False, f"PDF çok fazla sayfa içeriyor ({len(pdf.pages)} > 1000)"
        except Exception as e:
            return False, f"PDF bozuk veya okunamıyor: {str(e)[:100]}"

        return True, "OK"

    except Exception as e:
        return False, f"Beklenmeyen hata: {str(e)[:100]}"


def is_safe_path(base_dir: Path, target_path: Path) -> bool:
    """
    Path traversal saldırılarına karşı koruma.

    Args:
        base_dir: Güvenli temel dizin
        target_path: Kontrol edilecek hedef path

    Returns:
        Path güvenliyse True, değilse False

    Örnek saldırılar:
        - ../../../etc/passwd
        - /etc/passwd
        - symlink manipulation
        - \\\\network\\share\\malicious.pdf
    """
    try:
        # resolve() tüm symlink'leri ve .. işaretlerini çözer
        resolved_base = base_dir.resolve(strict=False)
        resolved_target = target_path.resolve(strict=False)

        # target, base'in altında mı?
        # Örnek: base=/home/user/krm, target=/home/user/krm/output/file.pdf → OK
        # Örnek: base=/home/user/krm, target=/etc/passwd → FAIL
        try:
            resolved_target.relative_to(resolved_base)
            return True
        except ValueError:
            # relative_to() hata verirse, target base'in dışında demektir
            return False

    except Exception:
        # Beklenmeyen hata durumunda güvenli tarafta kal
        return False


def safe_glob_pdfs(folder: Path, base_dir: Path) -> List[Path]:
    """
    Güvenli PDF listesi döndür (validation + path traversal koruması).

    Args:
        folder: Taranacak klasör
        base_dir: Güvenli temel dizin

    Returns:
        Güvenlik kontrolünden geçmiş PDF listesi
    """
    safe_pdfs = []

    try:
        # Klasör güvenli mi?
        if not is_safe_path(base_dir, folder):
            console.print(f"[red]⚠️  Güvenlik: Tehlikeli klasör atlandı: {folder}[/red]")
            return []

        # PDF'leri bul
        all_pdfs = list(folder.glob("*.pdf"))

        for pdf in all_pdfs:
            # 1. Path traversal kontrolü
            if not is_safe_path(base_dir, pdf):
                console.print(f"[red]⚠️  Güvenlik: Tehlikeli path atlandı: {pdf.name}[/red]")
                continue

            # 2. PDF validation
            is_valid, error_msg = validate_pdf_file(pdf)
            if not is_valid:
                console.print(f"[yellow]⚠️  Geçersiz PDF atlandı:[/yellow] {pdf.name}")
                console.print(f"[dim]   Sebep: {error_msg}[/dim]")
                continue

            safe_pdfs.append(pdf)

        return safe_pdfs

    except Exception as e:
        console.print(f"[red]Klasör tarama hatası: {e}[/red]")
        return []

def register_fonts() -> bool:
    """
    Türkçe karakter desteği için DejaVu Sans fontlarını kaydet.

    Fontlar proje içinde fonts/ dizininde bulunur.

    Returns:
        Font başarıyla yüklendiyse True, yoksa False
    """
    from reportlab.pdfbase.pdfmetrics import registerFontFamily

    try:
        # PyInstaller uyumluluğu için font dizinini bul
        if getattr(sys, 'frozen', False):
            # EXE olarak çalışıyorsa
            base_dir = Path(sys._MEIPASS)  # PyInstaller geçici dizini
            console.print(f"[dim]🔤 Font aranıyor (EXE modu): {base_dir}[/dim]")
        else:
            # Python script olarak çalışıyorsa
            base_dir = Path(__file__).parent
            console.print(f"[dim]🔤 Font aranıyor (Script modu): {base_dir}[/dim]")

        font_dir = base_dir / "fonts"
        font_normal = font_dir / "DejaVuSans.ttf"
        font_bold = font_dir / "DejaVuSans-Bold.ttf"

        console.print(f"[cyan]📁 Font dizini:[/cyan] {font_dir}")

        if not font_normal.exists():
            console.print(f"[red]✗ Font bulunamadı: {font_normal}[/red]")
            console.print(f"[yellow]  Lütfen DejaVu fontlarını fonts/ dizinine yerleştirin[/yellow]")
            console.print(f"[dim]  Font dizinindeki dosyalar:[/dim]")
            try:
                for f in font_dir.iterdir():
                    console.print(f"    → {f.name}")
            except:
                console.print(f"    [red]Dizin bulunamadı![/red]")
            return False

        # Normal font kaydı
        pdfmetrics.registerFont(TTFont('DejaVuSans', str(font_normal)))

        # Bold font kaydı
        if font_bold.exists():
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(font_bold)))
        else:
            # Bold yoksa normal fontı kullan
            pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', str(font_normal)))

        # Font ailesini kaydet
        registerFontFamily(
            'DejaVuSans',
            normal='DejaVuSans',
            bold='DejaVuSans-Bold',
            italic='DejaVuSans',  # Italic yoksa normal kullan
            boldItalic='DejaVuSans-Bold'
        )

        console.print(f"[green]✓ Türkçe font yüklendi: DejaVu Sans[/green]")
        return True

    except Exception as e:
        console.print(f"[red]✗ Font yükleme hatası: {e}[/red]")
        return False

def find_column_indices(header: List[Any], column_mapping: Dict[str, List[str]]) -> Dict[str, int]:
    """
    Dinamik kolon indeks bulucu.

    Args:
        header: Tablo başlık satırı
        column_mapping: Her kolon için aranacak string pattern'leri içeren dict

    Returns:
        Bulunan kolon indekslerini içeren dict

    Example:
        >>> header = ["Grup Limit", "Nakdi Limit", "Gayrinakdi Limit"]
        >>> mapping = {
        ...     'grup': ['grup limit'],
        ...     'nakdi': ['nakdi limit']
        ... }
        >>> find_column_indices(header, mapping)
        {'grup': 0, 'nakdi': 1}
    """
    indices = {}
    for key, patterns in column_mapping.items():
        for i, col in enumerate(header):
            col_str = str(col).replace('\n', ' ').lower().strip()
            if any(pattern in col_str for pattern in patterns):
                indices[key] = i
                break
    return indices

def ensure_output_dir(base_dir: Optional[Path] = None) -> Path:
    """
    Output dizinini oluştur.

    Args:
        base_dir: Output dizini oluşturulacak ana dizin (opsiyonel)

    Returns:
        Output dizininin Path objesi
    """
    if base_dir is None:
        # PyInstaller uyumluluğu: EXE'nin bulunduğu dizini bul
        if getattr(sys, 'frozen', False):
            # EXE olarak çalışıyorsa
            base_dir = Path(sys.executable).parent
        else:
            # Python script olarak çalışıyorsa
            base_dir = Path(__file__).parent

    output_dir = base_dir / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def find_folders_with_reports() -> Dict[Path, Dict[str, List[Path]]]:
    """
    Alt klasörlerdeki KRM ve Findeks PDF dosyalarını bul.

    GÜVENLİK: Path traversal ve PDF validation kontrolleri yapılır.

    Returns:
        Dict[klasör_path, {'krm': [pdf_list], 'findeks': [pdf_list]}]
    """
    # PyInstaller uyumluluğu: EXE'nin bulunduğu dizini bul
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys.executable).parent
        console.print(f"[dim]🔍 EXE modu: {base_dir}[/dim]")
    else:
        base_dir = Path(__file__).parent
        console.print(f"[dim]🔍 Script modu: {base_dir}[/dim]")

    console.print(f"[cyan]📂 Alt klasörler taranıyor:[/cyan] {base_dir}\n")

    folders_with_reports = {}

    # Alt klasörleri tara
    for folder in base_dir.iterdir():
        if not folder.is_dir():
            continue

        # output, fonts, .git gibi sistem klasörlerini atla
        if folder.name.startswith('.') or folder.name in ['output', 'fonts', '__pycache__']:
            continue

        # Bu klasördeki PDF'leri GÜVENLİ ŞEKİLDE bul
        all_pdfs = safe_glob_pdfs(folder, base_dir)

        if not all_pdfs:
            continue

        krm_pdfs = [pdf for pdf in all_pdfs if 'KRM' in pdf.name or 'krm' in pdf.name]
        findeks_pdfs = [pdf for pdf in all_pdfs if 'Findeks' in pdf.name or 'findeks' in pdf.name or 'FİNDEKS' in pdf.name]

        # En azından bir KRM varsa bu klasörü kaydet
        if krm_pdfs:
            folders_with_reports[folder] = {
                'krm': sorted(krm_pdfs),
                'findeks': sorted(findeks_pdfs)
            }

            console.print(f"[green]✓ {folder.name}/[/green]")
            console.print(f"  [cyan]KRM:[/cyan] {len(krm_pdfs)} adet")
            for pdf in krm_pdfs:
                console.print(f"    → {pdf.name}")
            if findeks_pdfs:
                console.print(f"  [yellow]Findeks:[/yellow] {len(findeks_pdfs)} adet")
                for pdf in findeks_pdfs:
                    console.print(f"    → {pdf.name}")
            console.print()

    if not folders_with_reports:
        console.print("[yellow]⚠ Hiçbir klasörde geçerli KRM PDF bulunamadı![/yellow]")
        console.print("[dim]Alt klasörler oluşturun ve içine KRM PDF'leri yerleştirin.[/dim]")

    return folders_with_reports

def show_folder_tree(folders: Dict[Path, Dict[str, List[Path]]]) -> None:
    """
    Bulunan klasörleri tree formatında göster.

    Args:
        folders: find_folders_with_reports() sonucu
    """
    if not folders:
        return

    tree = Tree("📂 [bold cyan]Bulunan Klasörler[/bold cyan]")

    for folder_path, pdfs_dict in folders.items():
        # Klasör dalı
        folder_branch = tree.add(f"[green]{folder_path.name}/[/green]")

        # KRM dosyaları
        if pdfs_dict['krm']:
            krm_branch = folder_branch.add("[cyan]📄 KRM Raporları[/cyan]")
            for pdf in pdfs_dict['krm']:
                size_mb = pdf.stat().st_size / (1024 * 1024)
                krm_branch.add(f"[white]{pdf.name}[/white] [dim]({size_mb:.1f} MB)[/dim]")

        # Findeks dosyaları
        if pdfs_dict['findeks']:
            findeks_branch = folder_branch.add("[yellow]📊 Findeks Raporları[/yellow]")
            for pdf in pdfs_dict['findeks']:
                size_mb = pdf.stat().st_size / (1024 * 1024)
                findeks_branch.add(f"[white]{pdf.name}[/white] [dim]({size_mb:.1f} MB)[/dim]")

        # Output klasörü (oluşturulacak)
        folder_branch.add("[dim]📁 output/ (oluşturulacak)[/dim]")

    console.print(tree)
    console.print()

def parse_header(pdf: pdfplumber.PDF) -> Tuple[str, str]:
    """
    PDF'den firma bilgilerini çıkar.

    Args:
        pdf: pdfplumber PDF objesi

    Returns:
        (firma_adi, rapor_tarihi) tuple'ı
    """
    try:
        first_page = pdf.pages[0]
        text = first_page.extract_text()

        lines = text.split('\n')
        company_name = ""
        for i, line in enumerate(lines):
            if 'KRM SORGU ÖZET RAPORU' in line and i + 1 < len(lines):
                company_name = lines[i + 1].strip()
                break

        import re
        date_match = re.search(r'Sorgu Tarihi\s+(\d{2}\.\d{2}\.\d{2})', text)
        report_date = date_match.group(1) if date_match else "Bilinmiyor"

        return company_name, report_date
    except:
        return "Bilinmeyen Firma", "Bilinmiyor"

def clean_number(value: Any) -> float:
    """
    Sayıları temizle ve float'a çevir.

    Args:
        value: Temizlenecek değer (str, int, float veya None)

    Returns:
        Temizlenmiş float değer, hata durumunda 0.0
    """
    if not value or value == '0':
        return 0.0
    try:
        cleaned = str(value).replace('\n', '').replace('.', '').replace(',', '.')
        return float(cleaned)
    except:
        return 0.0

def parse_date(date_str: Any) -> Optional[datetime]:
    """
    Tarih string'ini parse et.

    Args:
        date_str: Tarih string'i (dd/mm/yy veya dd/mm/yyyy formatında)

    Returns:
        datetime objesi veya None (parse edilemezse)
    """
    if not date_str or date_str == '':
        return None
    try:
        parts = str(date_str).strip().split('/')
        if len(parts) == 3:
            day, month, year = parts
            if len(year) == 2:
                year = '20' + year if int(year) < 50 else '19' + year
            return datetime(int(year), int(month), int(day))
    except:
        pass
    return None

def parse_tables(pdf: pdfplumber.PDF, cutoff_date: Optional[datetime] = None) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """
    Limit ve Risk tablolarını parse et.

    Args:
        pdf: pdfplumber PDF objesi
        cutoff_date: Pasif kaynak tespiti için cutoff tarihi (opsiyonel, default: 180 gün önce)

    Returns:
        (limits_dict, risks_dict) tuple'ı
    """
    limits: Dict[str, Dict[str, Any]] = {}
    risks: Dict[str, Dict[str, Any]] = {}

    if cutoff_date is None:
        cutoff_date = datetime.now() - timedelta(days=PASSIVE_SOURCE_CUTOFF_DAYS)

    for page_num in [1, 2]:
        try:
            page = pdf.pages[page_num]
            tables = page.extract_tables()

            for table in tables:
                if not table or len(table) < 2:
                    continue

                first_row = table[0] if table else []
                first_cell = str(first_row[0]) if first_row else ""

                # Limit tablosu
                if "LİMİT BİLGİLERİ" in first_cell and "RİSK" not in first_cell:
                    if len(table) < 3:
                        continue

                    header = table[1]

                    # Kolon indekslerini bul
                    limit_column_mapping = {
                        'grup': ['grup limit'],
                        'nakdi': ['nakdi limit'],
                        'gayrinakdi': ['gayrinakdi', 'limit'],
                        'toplam': ['toplam limit'],
                        'revize_vade': ['genel revize', 'revize vadesi'],
                        'son_revize': ['son revize']
                    }
                    indices = find_column_indices(header, limit_column_mapping)

                    grup_idx = indices.get('grup', -1)
                    nakdi_idx = indices.get('nakdi', -1)
                    gayrinakdi_idx = indices.get('gayrinakdi', -1)
                    toplam_idx = indices.get('toplam', -1)
                    revize_vade_idx = indices.get('revize_vade', -1)
                    son_revize_idx = indices.get('son_revize', -1)

                    for row in table[2:]:
                        if not row or not row[0] or 'KAYNAK-' not in str(row[0]):
                            continue

                        kaynak = str(row[0]).strip()

                        try:
                            revize_vade = parse_date(row[revize_vade_idx]) if revize_vade_idx >= 0 and len(row) > revize_vade_idx else None
                            son_revize = parse_date(row[son_revize_idx]) if son_revize_idx >= 0 and len(row) > son_revize_idx else None

                            latest_revize = None
                            if revize_vade and son_revize:
                                latest_revize = max(revize_vade, son_revize)
                            elif revize_vade:
                                latest_revize = revize_vade
                            elif son_revize:
                                latest_revize = son_revize

                            revize_gecmis = latest_revize and latest_revize < cutoff_date

                            limits[kaynak] = {
                                'grup': clean_number(row[grup_idx]) if grup_idx >= 0 and len(row) > grup_idx else 0,
                                'nakdi': clean_number(row[nakdi_idx]) if nakdi_idx >= 0 and len(row) > nakdi_idx else 0,
                                'gayrinakdi': clean_number(row[gayrinakdi_idx]) if gayrinakdi_idx >= 0 and len(row) > gayrinakdi_idx else 0,
                                'toplam': clean_number(row[toplam_idx]) if toplam_idx >= 0 and len(row) > toplam_idx else 0,
                                'revize_tarihi': latest_revize,
                                'revize_gecmis': revize_gecmis
                            }
                        except Exception as e:
                            continue

                # Risk tablosu
                elif "RİSK BİLGİLERİ" in first_cell:
                    if len(table) < 3:
                        continue

                    header = table[1]

                    # Kolon indekslerini bul
                    risk_column_mapping = {
                        'nakdi': ['nakdi risk'],
                        'gayrinakdi': ['gayrinakdi', 'risk'],
                        'toplam': ['toplam risk'],
                        'gecikme': ['max gecikme', 'gecikme gün']
                    }
                    indices = find_column_indices(header, risk_column_mapping)

                    nakdi_idx = indices.get('nakdi', -1)
                    gayrinakdi_idx = indices.get('gayrinakdi', -1)
                    toplam_idx = indices.get('toplam', -1)
                    gecikme_idx = indices.get('gecikme', -1)

                    for row in table[2:]:
                        if not row or not row[0] or 'KAYNAK-' not in str(row[0]):
                            continue

                        kaynak = str(row[0]).strip()

                        try:
                            risks[kaynak] = {
                                'nakdi': clean_number(row[nakdi_idx]) if nakdi_idx >= 0 and len(row) > nakdi_idx else 0,
                                'gayrinakdi': clean_number(row[gayrinakdi_idx]) if gayrinakdi_idx >= 0 and len(row) > gayrinakdi_idx else 0,
                                'toplam': clean_number(row[toplam_idx]) if toplam_idx >= 0 and len(row) > toplam_idx else 0,
                                'gecikme': int(clean_number(row[gecikme_idx])) if gecikme_idx >= 0 and len(row) > gecikme_idx else 0,
                            }
                        except Exception as e:
                            continue

        except Exception as e:
            continue

    return limits, risks

def clean_bank_name_ocr(raw_name: str) -> str:
    """OCR hatalarını düzelt ve banka ismini temizle."""
    bank_mapping = {
        'garanti bbva': 'Garanti BBVA',
        'garanti': 'Garanti BBVA',
        'ddestekbank': 'DenizBank',
        'denizbank': 'DenizBank',
        'destekbank': 'DenizBank',
        'eprurolbank': 'ING Bank',
        'ing': 'ING Bank',
        'turkishbank': 'TurkishBank',
        'vakifbank': 'Vakıfbank',
        'vakif': 'Vakıfbank',
        'anadolubank': 'Anadolubank',
        'anadolu': 'Anadolubank',
        'qnb': 'QNB Finansbank',
        'yanikredi': 'Yapı Kredi',
        'yapikredi': 'Yapı Kredi',
        'yapi kredi': 'Yapı Kredi',
        'ziraat': 'Ziraat Bankası',
        'halkbank': 'Halkbank',
        'halk': 'Halkbank',
        'isbank': 'İş Bankası',
        'is bankasi': 'İş Bankası',
        'akbank': 'Akbank',
        'akbanik': 'Akbank',
        'teb': 'TEB',
        'sekerbank': 'Şekerbank',
        'seker': 'Şekerbank',
        'finansbank': 'QNB Finansbank',
        'odeabank': 'Odeabank',
        'fibabanka': 'Fibabanka',
        'faktifbank': 'Aktifbank',
        'aktifbank': 'Aktifbank',
    }

    name_clean = raw_name.lower().strip()
    name_clean = re.sub(r'[^a-z\s]', '', name_clean)

    for key, value in bank_mapping.items():
        if key in name_clean:
            return value

    return raw_name.strip().title()

def parse_number_ocr(text: str) -> float:
    """OCR'dan gelen sayıları parse et."""
    if not text or text == '-':
        return 0.0
    try:
        cleaned = re.sub(r'[^\d]', '', text)
        return float(cleaned) if cleaned else 0.0
    except:
        return 0.0

def extract_findeks_data(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Findeks raporundan kurum bilgilerini OCR ile çıkar.

    Args:
        pdf_path: Findeks PDF dosyasının Path'i

    Returns:
        Her kurum için dict listesi (gerçek banka isimleriyle)
    """
    import re

    kurumlar = []

    try:
        # PyMuPDF ve pytesseract kullan
        import fitz
        import pytesseract
        from PIL import Image
        import shutil
        import sys
        import os

        # PyInstaller ile paketlenmiş EXE ise Tesseract path'ini ayarla
        if getattr(sys, 'frozen', False):
            # EXE içindeyiz
            base_path = sys._MEIPASS
            tesseract_cmd = os.path.join(base_path, 'tesseract.exe')
            if os.path.exists(tesseract_cmd):
                pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
                # Tessdata path'ini de ayarla
                os.environ['TESSDATA_PREFIX'] = os.path.join(base_path, 'tessdata')

        # Tesseract binary'sinin varlığını kontrol et
        tesseract_available = False
        try:
            pytesseract.get_tesseract_version()
            tesseract_available = True
        except:
            tesseract_available = shutil.which('tesseract') is not None

        if not tesseract_available:
            console.print(f"[yellow]⚠ Tesseract OCR bulunamadı. Findeks eşleştirmesi devre dışı.[/yellow]")
            console.print(f"[dim]Tesseract kurmak için: https://github.com/tesseract-ocr/tesseract[/dim]")
            return []

        pdf = fitz.open(str(pdf_path))

        for page_num in range(2, len(pdf)):
            try:
                page = pdf[page_num]

                # Yüksek çözünürlükte render
                mat = fitz.Matrix(2.5, 2.5)
                pix = page.get_pixmap(matrix=mat)
                img = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)

                # OCR yap
                text = pytesseract.image_to_string(img, lang='eng')

                # "Toplam" kelimesinin önündeki banka isimlerini bul
                toplam_lines = re.findall(r'(.{5,40})\s+Toplam\s+[\d.,]+', text)

                for bank_candidate in toplam_lines:
                    bank_candidate = re.sub(r'^[^a-zA-Z]+', '', bank_candidate).strip()

                    # Banka anahtar kelimeleri
                    if not any(keyword in bank_candidate.lower() for keyword in
                              ['bank', 'vakif', 'garanti', 'destekbank', 'deniz', 'ing', 'qnb',
                               'yapi', 'kredi', 'anadolu', 'turkish', 'seker', 'halk', 'ziraat',
                               'teb', 'akb', 'odea', 'fiba', 'aktif', 'faktif']):
                        continue

                    bank_name = clean_bank_name_ocr(bank_candidate)

                    # Banka için limit/risk bloğunu bul
                    bank_pos = text.find(bank_candidate)
                    if bank_pos == -1:
                        continue

                    block = text[max(0, bank_pos-200):bank_pos+800]

                    # Limit ve Risk değerlerini parse et
                    grup_limit_match = re.search(r'Grup\s+([\d.,]+)', block)
                    nakdi_limit_match = re.search(r'Nakdi\s+([\d.,]+)', block)
                    gayri_limit_match = re.search(r'Gayri\s+Nakdi\s+([\d.,]+)', block)
                    toplam_limit_match = re.search(r'Toplam\s+([\d.,]+)', block)

                    # Risk değerleri
                    risk_section = block[block.find('RISK (TL)'):] if 'RISK (TL)' in block else block
                    nakdi_risk_matches = re.findall(r'Nakdi\s+([\d.,]+)', risk_section)
                    gayri_risk_matches = re.findall(r'Gayri\s+Nakdi\s+([\d.,]+)', risk_section)
                    toplam_risk_matches = re.findall(r'Toplam\s+([\d.,]+)', risk_section)

                    kurum_data = {
                        'sayfa': page_num + 1,
                        'kurum': bank_name,
                        'grup_limit': parse_number_ocr(grup_limit_match.group(1)) if grup_limit_match else 0.0,
                        'nakdi_limit': parse_number_ocr(nakdi_limit_match.group(1)) if nakdi_limit_match else 0.0,
                        'gayrinakdi_limit': parse_number_ocr(gayri_limit_match.group(1)) if gayri_limit_match else 0.0,
                        'toplam_limit': parse_number_ocr(toplam_limit_match.group(1)) if toplam_limit_match else 0.0,
                        'nakdi_risk': parse_number_ocr(nakdi_risk_matches[-1]) if nakdi_risk_matches else 0.0,
                        'gayrinakdi_risk': parse_number_ocr(gayri_risk_matches[-1]) if gayri_risk_matches else 0.0,
                        'toplam_risk': parse_number_ocr(toplam_risk_matches[-1]) if toplam_risk_matches else 0.0,
                        'revize_tarihi': None,
                    }

                    if any([kurum_data['nakdi_limit'], kurum_data['gayrinakdi_limit'],
                           kurum_data['nakdi_risk'], kurum_data['gayrinakdi_risk']]):
                        kurumlar.append(kurum_data)

            except Exception as e:
                console.print(f"[dim]Sayfa {page_num+1} OCR hatası: {e}[/dim]")
                continue

        pdf.close()

    except Exception as e:
        console.print(f"[yellow]⚠ Findeks OCR hatası: {e}[/yellow]")
        console.print(f"[dim]PyMuPDF ve pytesseract gerekli. Kurulum: pip install PyMuPDF pytesseract[/dim]")

    return kurumlar

def calculate_match_score(krm_data: Dict[str, Any], findeks_data: Dict[str, Any]) -> float:
    """
    İki kaynak arasındaki benzerlik skorunu hesapla (düşük = iyi).

    Args:
        krm_data: KRM kaynak bilgileri
        findeks_data: Findeks kurum bilgileri

    Returns:
        Toplam fark skoru
    """
    score = 0.0
    match_count = 0

    # Nakdi Limit
    krm_nakdi_limit = krm_data.get('nakdi_limit', 0)
    findeks_nakdi_limit = findeks_data.get('nakdi_limit', 0)
    if krm_nakdi_limit > 0 and findeks_nakdi_limit > 0:
        diff = abs(krm_nakdi_limit - findeks_nakdi_limit) / max(krm_nakdi_limit, findeks_nakdi_limit)
        score += diff * 2
        match_count += 1

    # Gayrinakdi Limit
    krm_gayri_limit = krm_data.get('gayrinakdi_limit', 0)
    findeks_gayri_limit = findeks_data.get('gayrinakdi_limit', 0)
    if krm_gayri_limit > 0 and findeks_gayri_limit > 0:
        diff = abs(krm_gayri_limit - findeks_gayri_limit) / max(krm_gayri_limit, findeks_gayri_limit)
        score += diff * 1.5
        match_count += 1

    # Nakdi Risk
    krm_nakdi_risk = krm_data.get('nakdi_risk', 0)
    findeks_nakdi_risk = findeks_data.get('nakdi_risk', 0)
    if krm_nakdi_risk > 0 and findeks_nakdi_risk > 0:
        diff = abs(krm_nakdi_risk - findeks_nakdi_risk) / max(krm_nakdi_risk, findeks_nakdi_risk)
        score += diff * 2
        match_count += 1

    # Gayrinakdi Risk
    krm_gayri_risk = krm_data.get('gayrinakdi_risk', 0)
    findeks_gayri_risk = findeks_data.get('gayrinakdi_risk', 0)
    if krm_gayri_risk > 0 and findeks_gayri_risk > 0:
        diff = abs(krm_gayri_risk - findeks_gayri_risk) / max(krm_gayri_risk, findeks_gayri_risk)
        score += diff * 1.5
        match_count += 1

    # Toplam Limit
    krm_toplam_limit = krm_data.get('toplam_limit', 0)
    findeks_toplam_limit = findeks_data.get('toplam_limit', 0)
    if krm_toplam_limit > 0 and findeks_toplam_limit > 0:
        diff = abs(krm_toplam_limit - findeks_toplam_limit) / max(krm_toplam_limit, findeks_toplam_limit)
        score += diff * 1
        match_count += 1

    if match_count == 0:
        return float('inf')

    avg_score = score / match_count
    if match_count < 2:
        avg_score *= 2

    return avg_score

def find_best_matches(
    krm_sources: Dict[str, Dict[str, Any]],
    krm_risks: Dict[str, Dict[str, Any]],
    findeks_data: List[Dict[str, Any]],
    threshold: float = FINDEKS_MATCH_THRESHOLD
) -> List[Dict[str, Any]]:
    """
    KRM kaynakları ile Findeks kurumlarını eşleştir.

    Args:
        krm_sources: KRM limit bilgileri
        krm_risks: KRM risk bilgileri
        findeks_data: Findeks kurum listesi
        threshold: Maksimum fark yüzdesi

    Returns:
        Eşleştirme sonuçları listesi
    """
    matches = []

    for kaynak, limit_data in krm_sources.items():
        risk_data = krm_risks.get(kaynak, {})

        krm_combined = {
            'nakdi_limit': limit_data.get('nakdi', 0),
            'gayrinakdi_limit': limit_data.get('gayrinakdi', 0),
            'toplam_limit': limit_data.get('toplam', 0),
            'nakdi_risk': risk_data.get('nakdi', 0),
            'gayrinakdi_risk': risk_data.get('gayrinakdi', 0),
            'toplam_risk': risk_data.get('toplam', 0),
        }

        best_match = None
        best_score = float('inf')

        for findeks_inst in findeks_data:
            score = calculate_match_score(krm_combined, findeks_inst)
            if score < best_score:
                best_score = score
                best_match = findeks_inst

        if best_score <= threshold and best_match:
            if best_score <= 0.05:
                confidence = 'HIGH'
            elif best_score <= 0.10:
                confidence = 'MEDIUM'
            else:
                confidence = 'LOW'

            matches.append({
                'krm_kaynak': kaynak,
                'findeks_kurum': best_match['kurum'],
                'findeks_sayfa': best_match['sayfa'],
                'score': best_score,
                'confidence': confidence,
                'krm_data': krm_combined,
                'findeks_data': best_match,
            })

    matches.sort(key=lambda x: x['score'])
    return matches

def identify_passive_sources(limits: Dict[str, Dict[str, Any]], risks: Dict[str, Dict[str, Any]]) -> List[str]:
    """
    Pasif kaynakları belirle.

    Args:
        limits: Limit bilgileri dict'i
        risks: Risk bilgileri dict'i

    Returns:
        Pasif kaynak isimlerinin listesi
    """
    passive = []

    for kaynak in limits.keys():
        limit_data = limits.get(kaynak, {})
        risk_data = risks.get(kaynak, {})

        toplam_limit = limit_data.get('toplam', 0)
        toplam_risk = risk_data.get('toplam', 0)
        revize_gecmis = limit_data.get('revize_gecmis', False)

        if revize_gecmis and toplam_limit == 0 and toplam_risk == 0:
            passive.append(kaynak)

    return passive

def find_anomalies(limits: Dict[str, Dict[str, Any]], risks: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Tutarsızlıkları ve sorunları tespit et.

    Args:
        limits: Limit bilgileri dict'i
        risks: Risk bilgileri dict'i

    Returns:
        Anomali dict'lerinin listesi (severity'ye göre sıralı)
    """
    anomalies: List[Dict[str, Any]] = []
    all_sources = set(list(limits.keys()) + list(risks.keys()))

    for kaynak in all_sources:
        limit_data = limits.get(kaynak, {})
        risk_data = risks.get(kaynak, {})

        grup_limit = limit_data.get('grup', 0)
        nakdi_limit = limit_data.get('nakdi', 0)
        nakdi_risk = risk_data.get('nakdi', 0)
        gayrinakdi_limit = limit_data.get('gayrinakdi', 0)
        gayrinakdi_risk = risk_data.get('gayrinakdi', 0)
        toplam_limit = limit_data.get('toplam', 0)
        toplam_risk = risk_data.get('toplam', 0)
        gecikme = risk_data.get('gecikme', 0)

        # 1. Nakdi limit aşımı
        if nakdi_risk > nakdi_limit and nakdi_limit > 0:
            asim = nakdi_risk - nakdi_limit

            if toplam_limit > 0 and nakdi_risk <= toplam_limit:
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'NAKDİ LİMİT YETERSİZ',
                    'severity': 'WARNING',
                    'detail': f'Nakdi risk ({nakdi_risk:,.0f}) nakdi limiti ({nakdi_limit:,.0f}) aşıyor, ancak toplam limit ({toplam_limit:,.0f}) yeterli. Nakdi aşım: {asim:,.0f} TL',
                    'value': asim
                })
            else:
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'NAKDİ LİMİT AŞIMI',
                    'severity': 'CRITICAL',
                    'detail': f'Nakdi risk ({nakdi_risk:,.0f}) nakdi limiti ({nakdi_limit:,.0f}) aşıyor. Aşım: {asim:,.0f} TL',
                    'value': asim
                })

        # 2. Gayrinakdi limit aşımı
        if gayrinakdi_risk > gayrinakdi_limit and gayrinakdi_limit > 0:
            asim = gayrinakdi_risk - gayrinakdi_limit

            if toplam_limit > 0 and gayrinakdi_risk > toplam_limit:
                asim_genel = gayrinakdi_risk - toplam_limit
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'GAYRİNAKDİ LİMİT AŞIMI',
                    'severity': 'CRITICAL',
                    'detail': f'Gayrinakdi risk ({gayrinakdi_risk:,.0f}) hem gayrinakdi limiti ({gayrinakdi_limit:,.0f}) hem de genel limiti ({toplam_limit:,.0f}) aşıyor. Genel limit aşımı: {asim_genel:,.0f} TL',
                    'value': asim_genel
                })
            else:
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'GAYRİNAKDİ LİMİT AŞIMI',
                    'severity': 'WARNING',
                    'detail': f'Gayrinakdi risk ({gayrinakdi_risk:,.0f}) gayrinakdi limiti ({gayrinakdi_limit:,.0f}) aşıyor ama genel limit ({toplam_limit:,.0f}) içinde. Gayrinakdi aşım: {asim:,.0f} TL',
                    'value': asim
                })

        # 3. Limitsiz kullanım
        if toplam_risk > 0 and toplam_limit == 0:
            anomalies.append({
                'kaynak': kaynak,
                'type': 'LIMITSIZ KULLANIM',
                'severity': 'CRITICAL',
                'detail': f'Limit olmadan {toplam_risk:,.0f} TL risk taşınıyor',
                'value': toplam_risk
            })

        # 4. Gecikme
        if gecikme > 0:
            anomalies.append({
                'kaynak': kaynak,
                'type': 'GECIKME',
                'severity': 'CRITICAL' if gecikme > CRITICAL_DELAY_DAYS else 'WARNING',
                'detail': f'{gecikme} gun gecikme var',
                'value': gecikme
            })

        # 5. Yüksek kullanım / Toplam limit aşımı
        if toplam_limit > 0:
            kullanim = (toplam_risk / toplam_limit) * 100
            if kullanim > CRITICAL_USAGE_THRESHOLD:
                asim = toplam_risk - toplam_limit
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'TOPLAM LIMIT ASIMI',
                    'severity': 'CRITICAL',
                    'detail': f'Toplam risk ({toplam_risk:,.0f}) toplam limiti ({toplam_limit:,.0f}) asiyor. Asim: {asim:,.0f} TL (%{kullanim:.1f} kullanim)',
                    'value': asim
                })
            elif kullanim > HIGH_USAGE_THRESHOLD:
                anomalies.append({
                    'kaynak': kaynak,
                    'type': 'YUKSEK KULLANIM',
                    'severity': 'WARNING',
                    'detail': f'%{kullanim:.1f} kullanim (Risk: {toplam_risk:,.0f} / Limit: {toplam_limit:,.0f})',
                    'value': kullanim
                })

    return sorted(anomalies, key=lambda x: (0 if x['severity'] == 'CRITICAL' else 1, x['kaynak']))

def create_status_table(steps: List[Tuple[str, bool]], current_step: str) -> Table:
    """Live status için tablo oluştur."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Icon", width=3)
    table.add_column("Step", style="cyan")

    for step_name, done in steps:
        if done:
            icon = "[green]✓[/green]"
            style = "dim"
        elif step_name == current_step:
            icon = "[yellow]⏳[/yellow]"
            style = "bold yellow"
        else:
            icon = "[dim]○[/dim]"
            style = "dim"

        table.add_row(icon, f"[{style}]{step_name}[/{style}]")

    return table

def analyze_report(pdf_path: Path, findeks_pdf: Optional[Path] = None) -> Dict[str, Any]:
    """
    Tek bir PDF raporunu analiz et (opsiyonel Findeks eşleştirmesiyle).

    Live status ile her adımı görsel olarak gösterir.

    Args:
        pdf_path: Analiz edilecek PDF dosyasının Path'i
        findeks_pdf: Opsiyonel Findeks raporu Path'i

    Returns:
        Analiz sonuçlarını içeren dict
    """
    steps = [
        ("PDF Açılıyor", False),
        ("Header Parsing", False),
        ("Limit Tablosu", False),
        ("Risk Tablosu", False),
        ("Pasif Kaynak Tespiti", False),
        ("Anomali Taraması", False),
        ("Findeks Eşleştirme", False) if findeks_pdf else None,
    ]
    steps = [s for s in steps if s is not None]  # None'ları filtrele

    # Live display olmadan hızlı analiz yap
    # (Progress bar içinde zaten gösterge var, burada ek overhead istemiyoruz)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            company_name, report_date = parse_header(pdf)
            limits, risks = parse_tables(pdf)

            passive_sources = identify_passive_sources(limits, risks)

            all_sources = set(list(limits.keys()) + list(risks.keys()))
            active_sources = all_sources - set(passive_sources)

            active_limits = {k: v for k, v in limits.items() if k in active_sources}
            active_risks = {k: v for k, v in risks.items() if k in active_sources}

            anomalies = find_anomalies(active_limits, active_risks)

            # Findeks eşleştirmesi (varsa)
            findeks_matches = []
            if findeks_pdf and findeks_pdf.exists():
                try:
                    findeks_data = extract_findeks_data(findeks_pdf)
                    if findeks_data:
                        findeks_matches = find_best_matches(active_limits, active_risks, findeks_data)
                except Exception as e:
                    pass  # Sessizce devam et

            return {
                'pdf_name': pdf_path.name,
                'company_name': company_name,
                'report_date': report_date,
                'limits': limits,
                'risks': risks,
                'active_sources': list(active_sources),
                'passive_sources': passive_sources,
                'anomalies': anomalies,
                'findeks_matches': findeks_matches,
                'analysis_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                'success': True
            }
    except Exception as e:
        return {
            'pdf_name': pdf_path.name,
            'success': False,
            'error': str(e)
        }

def analyze_report_with_live_status(pdf_path: Path, findeks_pdf: Optional[Path] = None, show_live: bool = False) -> Dict[str, Any]:
    """
    Analiz et ve isteğe bağlı olarak live status göster.

    Args:
        pdf_path: PDF dosya yolu
        findeks_pdf: Findeks PDF (opsiyonel)
        show_live: Live status gösterilsin mi?

    Returns:
        Analiz sonuçları
    """
    if not show_live:
        # Normal analiz (hızlı)
        return analyze_report(pdf_path, findeks_pdf)

    # Live status ile analiz
    steps = [
        ("PDF Açılıyor", False),
        ("Header Parsing", False),
        ("Limit Tablosu", False),
        ("Risk Tablosu", False),
        ("Pasif Kaynak", False),
        ("Anomali Taraması", False),
    ]

    if findeks_pdf:
        steps.append(("Findeks Eşleştirme", False))

    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="status")
    )

    def update_layout(current_idx: int):
        # Header
        layout["header"].update(
            Panel(
                f"[bold cyan]🔍 {pdf_path.name}[/bold cyan]",
                border_style="cyan"
            )
        )

        # Status tablo
        current_steps = [(name, i < current_idx) for i, (name, _) in enumerate(steps)]
        current_name = steps[current_idx][0] if current_idx < len(steps) else "Tamamlandı"
        table = create_status_table(current_steps, current_name)
        layout["status"].update(Panel(table, title="İşlemler", border_style="blue"))

    try:
        with Live(layout, console=console, refresh_per_second=10) as live:
            import time

            # Adım 0: PDF Açma
            update_layout(0)
            time.sleep(0.3)
            with pdfplumber.open(pdf_path) as pdf:

                # Adım 1: Header
                update_layout(1)
                time.sleep(0.2)
                company_name, report_date = parse_header(pdf)

                # Adım 2-3: Tablolar
                update_layout(2)
                time.sleep(0.3)
                limits, risks = parse_tables(pdf)
                update_layout(3)
                time.sleep(0.2)

                # Adım 4: Pasif kaynak
                update_layout(4)
                time.sleep(0.2)
                passive_sources = identify_passive_sources(limits, risks)

                all_sources = set(list(limits.keys()) + list(risks.keys()))
                active_sources = all_sources - set(passive_sources)

                active_limits = {k: v for k, v in limits.items() if k in active_sources}
                active_risks = {k: v for k, v in risks.items() if k in active_sources}

                # Adım 5: Anomali
                update_layout(5)
                time.sleep(0.2)
                anomalies = find_anomalies(active_limits, active_risks)

                # Adım 6: Findeks (varsa)
                findeks_matches = []
                if findeks_pdf and findeks_pdf.exists():
                    update_layout(6)
                    time.sleep(0.3)
                    try:
                        findeks_data = extract_findeks_data(findeks_pdf)
                        if findeks_data:
                            findeks_matches = find_best_matches(active_limits, active_risks, findeks_data)
                    except:
                        pass

            # Tamamlandı göster
            update_layout(len(steps))
            time.sleep(0.5)

        return {
            'pdf_name': pdf_path.name,
            'company_name': company_name,
            'report_date': report_date,
            'limits': limits,
            'risks': risks,
            'active_sources': list(active_sources),
            'passive_sources': passive_sources,
            'anomalies': anomalies,
            'findeks_matches': findeks_matches,
            'analysis_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'success': True
        }
    except Exception as e:
        return {
            'pdf_name': pdf_path.name,
            'success': False,
            'error': str(e)
        }

def format_number(num: float) -> str:
    """
    Sayıyı Türkçe formatta formatla.

    Args:
        num: Formatlanacak sayı

    Returns:
        Türkçe format string (nokta ayırıcılı)
    """
    return f"{num:,.0f}".replace(',', '.')

def generate_pdf(result: Dict[str, Any], output_dir: Path) -> Path:
    """
    PDF rapor oluştur.

    Args:
        result: analyze_report() fonksiyonundan dönen sonuç dict'i
        output_dir: PDF'in kaydedileceği dizin

    Returns:
        Oluşturulan PDF dosyasının Path'i
    """
    def create_heading(text: str, font_bold: str) -> RLTable:
        """Türkçe karakterli başlık oluştur (Paragraph yerine Table kullan)"""
        heading = RLTable([[text]], colWidths=[17*cm])
        heading.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, 0), font_bold),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1a1a1a')),
            ('BOTTOMPADDING', (0, 0), (0, 0), 10),
        ]))
        return heading

    pdf_filename = Path(result['pdf_name']).stem + '.pdf'
    pdf_path = output_dir / pdf_filename

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )

    story = []
    styles = getSampleStyleSheet()

    # Türkçe font desteği için font adını belirle
    try:
        registered_fonts = pdfmetrics.getRegisteredFontNames()
        if 'DejaVuSans' in registered_fonts:
            font_name = 'DejaVuSans'
            font_name_bold = 'DejaVuSans-Bold'
        else:
            # Fallback to Helvetica (Türkçe karakterler düzgün görüntülenmeyebilir)
            font_name = 'Helvetica'
            font_name_bold = 'Helvetica-Bold'
            console.print("[yellow]⚠ DejaVu Sans yüklenmedi, Helvetica kullanılıyor[/yellow]")
    except:
        font_name = 'Helvetica'
        font_name_bold = 'Helvetica-Bold'

    # Başlık
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=font_name_bold,
        fontSize=18,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    # Başlık - Table kullan (Paragraph İ harfini yutuyor)
    baslik_table = RLTable([["KRM Analiz Raporu"]], colWidths=[17*cm])
    baslik_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), font_name_bold),
        ('FONTSIZE', (0, 0), (0, 0), 18),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.HexColor('#1a1a1a')),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (0, 0), 20),
    ]))
    story.append(baslik_table)
    story.append(Spacer(1, 0.5*cm))

    # Genel Bilgiler
    info_data = [
        ['Firma:', result['company_name']],
        ['Rapor Tarihi:', result['report_date']],
        ['Analiz Tarihi:', result['analysis_date']],
        ['Kaynak Dosya:', result['pdf_name']]
    ]

    info_table = RLTable(info_data, colWidths=[4*cm, 13*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), font_name_bold),
        ('FONTNAME', (1, 0), (1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(info_table)
    story.append(Spacer(1, 0.8*cm))

    # Özet İstatistikler
    story.append(create_heading("Özet İstatistikler", font_name_bold))
    story.append(Spacer(1, 0.3*cm))

    total_sources = len(result['active_sources']) + len(result['passive_sources'])
    active_count = len(result['active_sources'])
    passive_count = len(result['passive_sources'])
    total_anomalies = len(result['anomalies'])
    critical_count = len([a for a in result['anomalies'] if a['severity'] == 'CRITICAL'])
    warning_count = len([a for a in result['anomalies'] if a['severity'] == 'WARNING'])

    stats_data = [
        ['Toplam Kaynak:', str(total_sources)],
        ['Aktif Kaynak:', str(active_count)],
        ['Pasif Kaynak:', str(passive_count)],
        ['Tespit Edilen Sorun:', str(total_anomalies)],
        ['Kritik Sorunlar:', str(critical_count)],
        ['Uyarılar:', str(warning_count)]
    ]

    stats_table = RLTable(stats_data, colWidths=[6*cm, 6*cm])
    stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#e8f4f8')),
        ('BACKGROUND', (1, 4), (1, 4), colors.HexColor('#ffe6e6') if critical_count > 0 else colors.white),
        ('BACKGROUND', (1, 5), (1, 5), colors.HexColor('#fff9e6') if warning_count > 0 else colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), font_name_bold),
        ('FONTNAME', (1, 0), (1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(stats_table)
    story.append(Spacer(1, 0.8*cm))

    # Pasif Kaynaklar
    if result['passive_sources']:
        story.append(create_heading(f"Pasif Kaynaklar ({passive_count})", font_name_bold))
        story.append(Spacer(1, 0.3*cm))

        passive_data = [['Kaynak', 'Son Revize', 'Grup Limit', 'Toplam Limit', 'Durum']]

        for kaynak in sorted(result['passive_sources']):
            limit_data = result['limits'].get(kaynak, {})
            revize_tarihi = limit_data.get('revize_tarihi')
            revize_str = revize_tarihi.strftime('%d/%m/%Y') if revize_tarihi else 'Bilinmiyor'

            grup_limit = limit_data.get('grup', 0)
            toplam_limit = limit_data.get('toplam', 0)

            passive_data.append([
                kaynak,
                revize_str,
                format_number(grup_limit),
                format_number(toplam_limit),
                'Pasif'
            ])

        passive_table = RLTable(passive_data, colWidths=[2.5*cm, 2.5*cm, 3*cm, 3*cm, 2*cm])
        passive_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#d9d9d9')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
            ('FONTNAME', (0, 1), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 5),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('WORDWRAP', (0, 0), (-1, -1), True),
        ]))

        story.append(passive_table)
        story.append(Spacer(1, 0.8*cm))

    # Kritik Sorunlar - Paragraph ile wordwrap
    critical = [a for a in result['anomalies'] if a['severity'] == 'CRITICAL']
    if critical:
        story.append(create_heading("Kritik Sorunlar", font_name_bold))
        story.append(Spacer(1, 0.3*cm))

        # Paragraph için stil tanımla
        critical_style = ParagraphStyle(
            'CriticalStyle',
            fontName=font_name,
            fontSize=10,
            textColor=colors.HexColor('#cc0000'),
            leading=14,
            leftIndent=0,
            spaceBefore=0,
            spaceAfter=8,
        )

        # Her sorun için Paragraph kullan (otomatik wordwrap)
        for idx, a in enumerate(critical, 1):
            # HTML karakterlerini escape et (& < > " ')
            kaynak = a['kaynak'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            atype = a['type'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail = a['detail'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            text = f"• {kaynak} - {atype}<br/>&nbsp;&nbsp;{detail}"
            para = Paragraph(text, critical_style)
            story.append(para)

        story.append(Spacer(1, 0.5*cm))

    # Uyarılar - Paragraph ile wordwrap
    warnings = [a for a in result['anomalies'] if a['severity'] == 'WARNING']
    if warnings:
        story.append(create_heading("Uyarılar", font_name_bold))
        story.append(Spacer(1, 0.3*cm))

        # Paragraph için stil tanımla
        warning_style = ParagraphStyle(
            'WarningStyle',
            fontName=font_name,
            fontSize=10,
            textColor=colors.HexColor('#ff8800'),
            leading=14,
            leftIndent=0,
            spaceBefore=0,
            spaceAfter=8,
        )

        # Her uyarı için Paragraph kullan (otomatik wordwrap)
        for idx, a in enumerate(warnings, 1):
            # HTML karakterlerini escape et (& < > " ')
            kaynak = a['kaynak'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            atype = a['type'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            detail = a['detail'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

            text = f"• {kaynak} - {atype}<br/>&nbsp;&nbsp;{detail}"
            para = Paragraph(text, warning_style)
            story.append(para)

        story.append(Spacer(1, 0.5*cm))

    # Yeni sayfa - Detaylı Kaynak Bilgileri
    story.append(PageBreak())
    story.append(create_heading("Detaylı Aktif Kaynak Bilgileri", font_name_bold))
    story.append(Spacer(1, 0.3*cm))

    # Findeks eşleştirmelerini dict'e çevir (hızlı erişim için)
    findeks_matches = result.get('findeks_matches', [])
    findeks_map = {match['krm_kaynak']: match['findeks_kurum'] for match in findeks_matches}

    detail_data = [['Kaynak', 'Findeks\nKurum', 'Grup Limit', 'Nakdi\nLimit', 'Nakdi\nRisk', 'Gayri.\nLimit', 'Gayri.\nRisk', 'Top.\nLimit', 'Top.\nRisk', 'Kul.\n%']]

    for kaynak in sorted(result['active_sources']):
        limit_data = result['limits'].get(kaynak, {})
        risk_data = result['risks'].get(kaynak, {})

        grup_limit = limit_data.get('grup', 0)
        nakdi_limit = limit_data.get('nakdi', 0)
        nakdi_risk = risk_data.get('nakdi', 0)
        gayrinakdi_limit = limit_data.get('gayrinakdi', 0)
        gayrinakdi_risk = risk_data.get('gayrinakdi', 0)
        toplam_limit = limit_data.get('toplam', 0)
        toplam_risk = risk_data.get('toplam', 0)

        kullanim = (toplam_risk / toplam_limit * 100) if toplam_limit > 0 else 0

        # Findeks eşleştirmesini bul
        findeks_kurum = findeks_map.get(kaynak, '-')

        detail_data.append([
            kaynak,
            findeks_kurum,
            format_number(grup_limit),
            format_number(nakdi_limit),
            format_number(nakdi_risk),
            format_number(gayrinakdi_limit),
            format_number(gayrinakdi_risk),
            format_number(toplam_limit),
            format_number(toplam_risk),
            f"{kullanim:.1f}"
        ])

    detail_table = RLTable(detail_data, colWidths=[1.8*cm, 2.2*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1.6*cm, 1*cm])

    # Zebra stripes
    table_style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4472C4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), font_name_bold),
        ('FONTNAME', (0, 1), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ]

    # Add zebra stripes
    for i in range(1, len(detail_data)):
        if i % 2 == 0:
            table_style_commands.append(('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f0f0f0')))

    detail_table.setStyle(TableStyle(table_style_commands))

    story.append(detail_table)

    # Footer
    story.append(Spacer(1, 1*cm))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontName=font_name,
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    # Footer - basit Table (Türkçe ı ve ş var ama footer önemli değil)
    footer_table = RLTable([["Rapor otomatik olarak KRM Analiz Aracı v2 tarafından oluşturulmuştur."]], colWidths=[17*cm])
    footer_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, 0), font_name),
        ('FONTSIZE', (0, 0), (0, 0), 8),
        ('TEXTCOLOR', (0, 0), (0, 0), colors.grey),
        ('ALIGN', (0, 0), (0, 0), 'CENTER'),
    ]))
    story.append(footer_table)

    # Build PDF
    doc.build(story)

    return pdf_path

def print_single_report(result: Dict[str, Any]) -> None:
    """
    Tek rapor için terminal özeti yazdır.

    Args:
        result: analyze_report() fonksiyonundan dönen sonuç dict'i
    """
    if not result['success']:
        console.print(f"[red]✗[/red] {result['pdf_name']}: {result['error']}")
        return

    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(Panel.fit(
        f"[bold]{result['company_name']}[/bold]\n"
        f"Rapor Tarihi: {result['report_date']}\n"
        f"Dosya: {result['pdf_name']}",
        border_style="cyan"
    ))

    anomalies = result['anomalies']
    active_count = len(result['active_sources'])
    passive_count = len(result['passive_sources'])

    console.print(f"\n[bold]📊 Özet:[/bold]")
    console.print(f"  Toplam Kaynak: {active_count + passive_count}")
    console.print(f"  [green]✅ Aktif Kaynak: {active_count}[/green]")
    if passive_count > 0:
        console.print(f"  [dim]💤 Pasif Kaynak: {passive_count}[/dim]")
    console.print(f"  Tespit Edilen Sorun: {len(anomalies)}")

    critical = [a for a in anomalies if a['severity'] == 'CRITICAL']
    warnings = [a for a in anomalies if a['severity'] == 'WARNING']

    if critical:
        console.print(f"  [red]Kritik: {len(critical)}[/red]")
    if warnings:
        console.print(f"  [yellow]Uyarı: {len(warnings)}[/yellow]")

    if passive_count > 0:
        console.print(f"\n[bold dim]💤 Pasif Kaynaklar ({passive_count}):[/bold dim]")

        passive_table = Table(title="Pasif Kaynaklar - Revize Vadesi Gecmis", border_style="dim", show_header=True)
        passive_table.add_column("Kaynak", style="dim cyan", width=12)
        passive_table.add_column("Son Revize", style="dim yellow", width=12)
        passive_table.add_column("Grup Limit", style="dim", width=15, justify="right")
        passive_table.add_column("Toplam Limit", style="dim", width=15, justify="right")
        passive_table.add_column("Durum", style="dim red", width=10)

        for kaynak in sorted(result['passive_sources']):
            limit_data = result['limits'].get(kaynak, {})
            revize_tarihi = limit_data.get('revize_tarihi')
            revize_str = revize_tarihi.strftime('%d/%m/%Y') if revize_tarihi else 'Bilinmiyor'

            grup_limit = limit_data.get('grup', 0)
            toplam_limit = limit_data.get('toplam', 0)

            passive_table.add_row(
                kaynak,
                revize_str,
                f"{grup_limit:,.0f}",
                f"{toplam_limit:,.0f}",
                "❌ Pasif"
            )

        console.print(passive_table)

    if anomalies:
        console.print(f"\n[bold]🚨 Tespit Edilen Sorunlar:[/bold]")

        if critical:
            table = Table(title="KRITIK", border_style="red", show_header=True)
            table.add_column("Kaynak", style="cyan", width=15)
            table.add_column("Tip", style="yellow", width=25)
            table.add_column("Detay", style="white")

            for a in critical:
                table.add_row(a['kaynak'], a['type'], a['detail'])

            console.print(table)

        if warnings:
            console.print()
            table = Table(title="UYARI", border_style="yellow", show_header=True)
            table.add_column("Kaynak", style="cyan", width=15)
            table.add_column("Tip", style="yellow", width=25)
            table.add_column("Detay", style="white")

            for a in warnings:
                table.add_row(a['kaynak'], a['type'], a['detail'])

            console.print(table)
    else:
        console.print(f"\n[bold green]✅ Aktif kaynaklarda tutarsizlik tespit edilmedi[/bold green]")

def main() -> None:
    """
    Ana program fonksiyonu.

    Alt klasörleri tarar, her klasördeki KRM ve Findeks raporlarını analiz eder.
    """
    console.print(Panel.fit(
        "[bold cyan]KRM Rapor Analiz Aracı v3[/bold cyan]\n"
        f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        "[dim]Klasör bazlı analiz, Findeks eşleştirmesi, PDF raporlama[/dim]",
        border_style="cyan"
    ))

    # Türkçe font desteğini aktifleştir
    register_fonts()

    # Alt klasörlerdeki raporları bul
    folders_with_reports = find_folders_with_reports()

    if not folders_with_reports:
        console.print("[red]✗ Analiz edilecek klasör bulunamadı![/red]")
        return

    # Tree view ile klasör yapısını göster
    show_folder_tree(folders_with_reports)

    console.print(f"[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold]Toplam {len(folders_with_reports)} klasör işlenecek[/bold]\n")

    # Her klasör için analiz yap
    all_results = []

    # Progress bar ile analiz
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(complete_style="green", finished_style="bold green"),
        TaskProgressColumn(),
        TextColumn("•"),
        TimeRemainingColumn(),
        console=console,
        transient=False
    ) as progress:

        # Ana klasör progress task'ı
        folder_task = progress.add_task(
            "[cyan]📂 Klasörler işleniyor...",
            total=len(folders_with_reports)
        )

        for folder_idx, (folder, pdfs_dict) in enumerate(folders_with_reports.items(), 1):
            # Klasör bilgisi göster
            progress.console.print(f"\n[bold cyan]{'='*60}[/bold cyan]")
            progress.console.print(f"[bold]KLASÖR {folder_idx}/{len(folders_with_reports)}: {folder.name}[/bold]")
            progress.console.print(f"[bold cyan]{'='*60}[/bold cyan]")

            # Bu klasör için output dizini oluştur
            output_dir = ensure_output_dir(folder)

            # Bu klasördeki Findeks raporunu seç (varsa ilkini al)
            findeks_pdf = pdfs_dict['findeks'][0] if pdfs_dict['findeks'] else None

            if findeks_pdf:
                progress.console.print(f"[cyan]🔗 Findeks:[/cyan] {findeks_pdf.name}")
            else:
                progress.console.print("[dim]📝 Findeks raporu yok[/dim]")

            progress.console.print()

            # Bu klasördeki her KRM raporunu analiz et
            folder_results = []
            krm_pdfs = pdfs_dict['krm']

            # PDF progress task'ı (her klasör için yeni)
            pdf_task = progress.add_task(
                f"[yellow]  ↳ PDF'ler işleniyor...",
                total=len(krm_pdfs)
            )

            for pdf_idx, krm_pdf in enumerate(krm_pdfs, 1):
                # Mevcut PDF'i göster
                progress.update(
                    pdf_task,
                    description=f"[yellow]  ↳ {krm_pdf.name[:40]}..."
                )

                # İlk klasörün ilk PDF'i için live status göster (demo)
                show_live = (folder_idx == 1 and pdf_idx == 1)
                result = analyze_report_with_live_status(krm_pdf, findeks_pdf, show_live=show_live)
                folder_results.append(result)
                all_results.append({
                    'folder': folder.name,
                    'result': result
                })

                if result['success']:
                    pdf_output = generate_pdf(result, output_dir)
                    progress.console.print(f"    [green]✓ {krm_pdf.name}[/green]")
                else:
                    progress.console.print(f"    [red]✗ {krm_pdf.name}: {result.get('error', 'Hata')}[/red]")

                # PDF progress'i güncelle
                progress.update(pdf_task, advance=1)

            # PDF task'ı tamamla ve gizle
            progress.update(pdf_task, visible=False)
            progress.remove_task(pdf_task)

            # Bu klasör için özet
            progress.console.print(f"\n[bold]📊 {folder.name} - Özet:[/bold]")
            for result in folder_results:
                if result['success']:
                    print_single_report(result)

            # Klasör progress'i güncelle
            progress.update(folder_task, advance=1)

        # Ana task tamamlandı
        progress.update(folder_task, description="[bold green]✓ Tüm klasörler tamamlandı!")

    # Genel özet
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold]GENEL ÖZET - TÜM KLASÖRLER[/bold]")
    console.print(f"[bold cyan]{'='*80}[/bold cyan]\n")

    successful_results = [r['result'] for r in all_results if r['result']['success']]

    total_folders = len(folders_with_reports)
    total_reports = len(all_results)
    total_active = sum(len(r['active_sources']) for r in successful_results)
    total_passive = sum(len(r['passive_sources']) for r in successful_results)
    total_critical = sum(len([a for a in r['anomalies'] if a['severity'] == 'CRITICAL']) for r in successful_results)
    total_warnings = sum(len([a for a in r['anomalies'] if a['severity'] == 'WARNING']) for r in successful_results)

    console.print(f"İşlenen Klasör Sayısı: [cyan]{total_folders}[/cyan]")
    console.print(f"Analiz Edilen Rapor: [cyan]{total_reports}[/cyan]")
    console.print(f"Toplam Aktif Kaynak: [green]{total_active}[/green]")
    console.print(f"Toplam Pasif Kaynak: [dim]{total_passive}[/dim]")
    console.print(f"Toplam Kritik Sorun: [red]{total_critical}[/red]")
    console.print(f"Toplam Uyarı: [yellow]{total_warnings}[/yellow]")

    if total_critical == 0 and total_warnings == 0:
        console.print("\n[bold green]🎉 Tüm raporlar temiz![/bold green]")

    console.print(f"\n[green]✓ Tüm PDF raporlar ilgili klasörlerdeki output/ dizinlerine kaydedildi[/green]")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n[bold red]HATA:[/bold red] {str(e)}")
        console.print("\n[yellow]Detaylar:[/yellow]")
        import traceback
        console.print(traceback.format_exc())
    finally:
        # EXE'de hızla kapanmasını engelle
        console.print("\n[dim]Çıkmak için Enter tuşuna basın...[/dim]")
        input()
