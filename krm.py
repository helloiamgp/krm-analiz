#!/usr/bin/env python3
"""
KRM Rapor Analiz Aracı
PDF çıktı ile profesyonel raporlama

Gereksinimler:
    pip install pdfplumber reportlab

Kullanım:
    python krm.py                  # Dizindeki tüm PDF'leri analiz et
    python krm.py rapor.pdf        # Sadece belirtilen PDF'i analiz et
"""

import pdfplumber
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import track

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

console = Console()

def register_fonts() -> bool:
    """
    Türkçe karakter desteği için DejaVu Sans fontlarını kaydet.

    Fontlar proje içinde fonts/ dizininde bulunur.

    Returns:
        Font başarıyla yüklendiyse True, yoksa False
    """
    from reportlab.pdfbase.pdfmetrics import registerFontFamily

    try:
        # Proje içindeki fonts dizini
        font_dir = Path(__file__).parent / "fonts"

        font_normal = font_dir / "DejaVuSans.ttf"
        font_bold = font_dir / "DejaVuSans-Bold.ttf"

        if not font_normal.exists():
            console.print(f"[red]✗ Font bulunamadı: {font_normal}[/red]")
            console.print(f"[yellow]  Lütfen DejaVu fontlarını fonts/ dizinine yerleştirin[/yellow]")
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

def ensure_output_dir() -> Path:
    """
    Output dizinini oluştur.

    Returns:
        Output dizininin Path objesi
    """
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir

def find_pdfs() -> List[Path]:
    """
    Mevcut dizindeki tüm PDF dosyalarını bul.

    Returns:
        Sıralı PDF dosya Path listesi
    """
    current_dir = Path(__file__).parent
    pdfs = list(current_dir.glob("*.pdf"))
    return sorted(pdfs)

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

def analyze_report(pdf_path: Path) -> Dict[str, Any]:
    """
    Tek bir PDF raporunu analiz et.

    Args:
        pdf_path: Analiz edilecek PDF dosyasının Path'i

    Returns:
        Analiz sonuçlarını içeren dict
    """
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
            
            return {
                'pdf_name': pdf_path.name,
                'company_name': company_name,
                'report_date': report_date,
                'limits': limits,
                'risks': risks,
                'active_sources': list(active_sources),
                'passive_sources': passive_sources,
                'anomalies': anomalies,
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
    
    # Kritik Sorunlar - Liste formatında
    critical = [a for a in result['anomalies'] if a['severity'] == 'CRITICAL']
    if critical:
        story.append(create_heading("Kritik Sorunlar", font_name_bold))
        story.append(Spacer(1, 0.3*cm))

        # Her sorun için ayrı kutu
        for idx, a in enumerate(critical, 1):
            problem_data = [
                [f"🔴 Sorun {idx}: {a['kaynak']}"],
                [f"Tip: {a['type']}"],
                [f"{a['detail']}"]
            ]

            problem_table = RLTable(problem_data, colWidths=[17*cm])
            problem_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#cc0000')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.white),
                ('FONTNAME', (0, 0), (0, 0), font_name_bold),
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#ffe6e6')),
                ('FONTNAME', (0, 1), (0, 1), font_name_bold),
                ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#fff0f0')),
                ('FONTNAME', (0, 2), (0, 2), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cc0000')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(problem_table)
            story.append(Spacer(1, 0.3*cm))

        story.append(Spacer(1, 0.5*cm))
    
    # Uyarılar - Liste formatında
    warnings = [a for a in result['anomalies'] if a['severity'] == 'WARNING']
    if warnings:
        story.append(create_heading("Uyarılar", font_name_bold))
        story.append(Spacer(1, 0.3*cm))

        # Her uyarı için ayrı kutu
        for idx, a in enumerate(warnings, 1):
            warning_data = [
                [f"⚠️ Uyarı {idx}: {a['kaynak']}"],
                [f"Tip: {a['type']}"],
                [f"{a['detail']}"]
            ]

            warning_table = RLTable(warning_data, colWidths=[17*cm])
            warning_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#ffcc00')),
                ('TEXTCOLOR', (0, 0), (0, 0), colors.black),
                ('FONTNAME', (0, 0), (0, 0), font_name_bold),
                ('BACKGROUND', (0, 1), (0, 1), colors.HexColor('#fff9e6')),
                ('FONTNAME', (0, 1), (0, 1), font_name_bold),
                ('BACKGROUND', (0, 2), (0, 2), colors.HexColor('#fffef0')),
                ('FONTNAME', (0, 2), (0, 2), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ffcc00')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))

            story.append(warning_table)
            story.append(Spacer(1, 0.3*cm))

        story.append(Spacer(1, 0.5*cm))
    
    # Yeni sayfa - Detaylı Kaynak Bilgileri
    story.append(PageBreak())
    story.append(create_heading("Detaylı Aktif Kaynak Bilgileri", font_name_bold))
    story.append(Spacer(1, 0.3*cm))
    
    detail_data = [['Kaynak', 'Grup Limit', 'Nakdi\nLimit', 'Nakdi\nRisk', 'Gayri.\nLimit', 'Gayri.\nRisk', 'Top.\nLimit', 'Top.\nRisk', 'Kul.\n%']]
    
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
        
        detail_data.append([
            kaynak,
            format_number(grup_limit),
            format_number(nakdi_limit),
            format_number(nakdi_risk),
            format_number(gayrinakdi_limit),
            format_number(gayrinakdi_risk),
            format_number(toplam_limit),
            format_number(toplam_risk),
            f"{kullanim:.1f}"
        ])
    
    detail_table = RLTable(detail_data, colWidths=[2*cm, 2*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.2*cm])
    
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

    Komut satırı argümanlarını parse eder ve PDF analiz işlemini başlatır.
    """
    console.print(Panel.fit(
        "[bold cyan]KRM Rapor Analiz Aracı v2[/bold cyan]\n"
        f"Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        "[dim]PDF raporlama ve pasif kaynak tespiti[/dim]",
        border_style="cyan"
    ))

    # Türkçe font desteğini aktifleştir
    register_fonts()

    output_dir = ensure_output_dir()
    
    if len(sys.argv) > 1:
        pdf_path = Path(sys.argv[1])
        if not pdf_path.exists():
            console.print(f"[red]Hata:[/red] {pdf_path} bulunamadi!")
            return
        
        console.print(f"\n[yellow]Analiz ediliyor: {pdf_path.name}[/yellow]")
        result = analyze_report(pdf_path)
        
        if result['success']:
            pdf_output = generate_pdf(result, output_dir)
            console.print(f"[green]✓[/green] PDF kaydedildi: {pdf_output}")
        
        print_single_report(result)
        return
    
    pdfs = find_pdfs()
    
    if not pdfs:
        console.print("[yellow]Bu dizinde PDF dosyasi bulunamadi![/yellow]")
        return
    
    console.print(f"\n[green]✓[/green] {len(pdfs)} adet PDF bulundu\n")
    
    results = []
    for pdf_path in track(pdfs, description="Analiz ediliyor..."):
        result = analyze_report(pdf_path)
        results.append(result)
        
        if result['success']:
            pdf_output = generate_pdf(result, output_dir)
    
    for result in results:
        print_single_report(result)
    
    console.print(f"\n[bold cyan]{'='*80}[/bold cyan]")
    console.print(f"[bold]GENEL ÖZET[/bold]")

    total_active = sum(len(r['active_sources']) for r in results if r['success'])
    total_passive = sum(len(r['passive_sources']) for r in results if r['success'])
    total_critical = sum(len([a for a in r['anomalies'] if a['severity'] == 'CRITICAL']) for r in results if r['success'])
    total_warnings = sum(len([a for a in r['anomalies'] if a['severity'] == 'WARNING']) for r in results if r['success'])

    console.print(f"Analiz Edilen Rapor: {len(results)}")
    console.print(f"Toplam Aktif Kaynak: [green]{total_active}[/green]")
    console.print(f"Toplam Pasif Kaynak: [dim]{total_passive}[/dim]")
    console.print(f"Toplam Kritik Sorun: [red]{total_critical}[/red]")
    console.print(f"Toplam Uyarı: [yellow]{total_warnings}[/yellow]")
    console.print(f"\n[green]✓[/green] PDF raporlar kaydedildi: {output_dir}/")
    
    if total_critical == 0 and total_warnings == 0:
        console.print("\n[bold green]🎉 Tüm aktif kaynaklar temiz![/bold green]")

if __name__ == "__main__":
    main()
