# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for FlowDictation Windows."""

import os
import sys
import importlib

block_cipher = None

# Locate customtkinter package data
ctk_path = os.path.dirname(importlib.import_module("customtkinter").__file__)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        (ctk_path, 'customtkinter'),
    ],
    hiddenimports=[
        'pystray._win32',
        'customtkinter',
        'PIL._tkinter_finder',
        'pygame',
        'sounddevice',
        'keyboard',
        'pyperclip',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'scipy', 'pandas', 'tkinter.test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FlowDictation',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,              # windowed, no console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,                  # add icon='resources/icon.ico' if you have one
)
