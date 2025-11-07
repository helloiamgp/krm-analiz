# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec dosyası - KRM Rapor Analiz Aracı v3

Bu dosya ile tek .exe dosyası oluşturulur.

Kullanım:
    pyinstaller krm.spec

Çıktı:
    dist/KRM-Analiz.exe  (veya KRM-Analiz - macOS/Linux için)
"""

block_cipher = None

a = Analysis(
    ['krm.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('fonts', 'fonts'),  # fonts/ klasörünü dahil et
    ],
    hiddenimports=[
        'pytesseract',
        'PIL',
        'PIL.Image',
        'pdfplumber',
        'reportlab',
        'rich',
        'fitz',  # PyMuPDF
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='KRM-Analiz',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Terminal penceresi göster
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # İkon eklemek için: icon='icon.ico'
)
