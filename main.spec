# -*- mode: python ; coding: utf-8 -*-
from sys import platform

if platform in ("win", "win32"):
    _plyer_module = "plyer.platforms.win.filechooser"
elif platform == "darwin":
    _plyer_module = "plyer.platforms.macosx.filechooser"
else:
    _plyer_module = "plyer.platforms.linux.filechooser"


block_cipher = None


a = Analysis(
    ['./main.py'],
    pathex=[],
    binaries=[],
    datas=[("assets/", "assets/")],
    hiddenimports=[_plyer_module, "tools.icon_def", "hover_behavior", "kivy.storage.jsonstore", "server", "toast",
    "netifaces"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["IPython", "ffpyplayer", "cv2", "enchant", "numpy", "PIL", "jnius", "gi", "dbus",
    "docutils", "email", "html", "http", "jinja2", "packaging", "pep517",
    "pkg_resources", "pydoc_data", "pygments", "pytoml", "unittest", "xml", "xmlrpc", "pyparsing"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Fleet',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Fleet',
)
