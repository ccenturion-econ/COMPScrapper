# -*- mode: python ; coding: utf-8 -*-
"""Especificación de PyInstaller para COMPScrapper.

Genera un ejecutable autónomo (onedir) y, en macOS, un bundle COMPScrapper.app.
Empaqueta los datos del motor (compscrapper/data: geografía de Paraguay, prompt
del asistente, sectores semilla). Se compila con:

    pyinstaller packaging/compscrapper.spec --noconfirm

Salida: dist/COMPScrapper.app (macOS) o dist/COMPScrapper/ (Windows).
"""

import os
import sys

# SPECPATH es el directorio de este .spec (lo define PyInstaller); la raíz del
# proyecto está un nivel arriba.
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

datas = [
    (os.path.join(ROOT, "compscrapper", "data"), os.path.join("compscrapper", "data")),
]

# bs4/openpyxl/requests se detectan por análisis estático; googlenewsdecoder hace
# algún import indirecto, lo incluimos explícito por las dudas.
hiddenimports = ["googlenewsdecoder"]

a = Analysis(
    [os.path.join(ROOT, "packaging", "launch.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.Qt3DCore"],
    noarchive=False,
)
pyz = PYZ(a.pure)

_ICONO_ICO = os.path.join(SPECPATH, "icono.ico")
_ICONO_ICNS = os.path.join(SPECPATH, "icono.icns")

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="COMPScrapper",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # app gráfica, sin consola
    icon=(_ICONO_ICO if sys.platform == "win32" else None),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="COMPScrapper",
)

# En macOS, envolver en un .app
if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="COMPScrapper.app",
        icon=_ICONO_ICNS,
        bundle_identifier="org.conacom.compscrapper",
        info_plist={
            "CFBundleName": "COMPScrapper",
            "CFBundleDisplayName": "COMPScrapper",
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
