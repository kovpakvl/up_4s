# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for SecureOffice Admin Console."""

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules


ROOT = Path(SPECPATH).resolve().parent

datas = []
datas += collect_data_files("customtkinter")
datas += collect_data_files("CTkMessagebox")
datas += collect_data_files("qrcode")
datas += [(str(ROOT / "docker-compose.yml"), ".")]
datas += [(str(ROOT / "backend" / "Dockerfile"), "backend")]
datas += [(str(ROOT / "backend" / "requirements.txt"), "backend")]

for path in (ROOT / "backend" / "secureoffice_backend").rglob("*"):
    if path.is_file():
        datas.append((str(path), str(path.parent.relative_to(ROOT))))

hiddenimports = []
hiddenimports += collect_submodules("PIL")
hiddenimports += collect_submodules("qrcode")

a = Analysis(
    [str(ROOT / "admin_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "pyinstaller"],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="SecureOfficeAdmin",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
