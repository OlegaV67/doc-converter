# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path
import customtkinter
import tkinterdnd2

ctk_path = Path(customtkinter.__file__).parent
dnd_path = Path(tkinterdnd2.__file__).parent

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        # CustomTkinter: темы, шрифты, изображения
        (str(ctk_path), 'customtkinter'),
        # tkinterdnd2: DLL для Drag & Drop
        (str(dnd_path), 'tkinterdnd2'),
        # Исходники приложения
        ('converters',  'converters'),
        ('core',        'core'),
        ('utils',       'utils'),
        ('ui',          'ui'),
    ],
    hiddenimports=[
        'customtkinter',
        'tkinterdnd2',
        'darkdetect',
        'packaging',
        'jwt',
        'requests',
        'certifi',
        'charset_normalizer',
        'urllib3',
        'idna',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='DocConverter_licensed',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # Без консольного окна
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    version_file=None,
)
