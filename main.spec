# -*- mode: python ; coding: utf-8 -*-
from sys import platform
#from os import environ
#environ["KIVY_DOC"] = "1"

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
    "netifaces", "pystray"],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["IPython", "ffpyplayer", "cv2", "enchant", "numpy", "jnius", "dbus",
    "docutils", "email", "html", "http", "jinja2", "packaging", "pep517",
    "pkg_resources", "pydoc_data", "pygments", "pytoml", "unittest", "xml", "xmlrpc", "pyparsing", "gstreamer",],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a.datas = [data for data in a.datas if not data[0].startswith("share")]
a.binaries = [bin for bin in a.binaries if not bin[0].startswith("gst_plugins") and not bin[0].startswith("lib/") \
and not bin[0].startswith("gi_typelibs") and not bin[0].startswith("libgst") and not bin[0].startswith("libav") \
and not bin[0].startswith("libb") and not bin[0].startswith("libv") and not bin[0].startswith("libw") \
and not bin[0].startswith("libfl") and not bin[0].startswith("gi_typelibs") and not bin[0].startswith("libk") \
and not bin[0].startswith("libi") and not bin[0].startswith("libh") and not bin[0].startswith("libd") \
and not bin[0].startswith("liba") and not bin[0].startswith("libc") and not bin[0].startswith("libe") \
and not bin[0].startswith("libz") and not bin[0].startswith("libu")]
from json import loads
with open("binaries.json") as f:
    b_list = loads(f.read())
#a.binaries = [bin for bin, binp in zip(a.binaries, b_list) if binp in bin[0]]
#bin_tmp_list = []
#for bin in a.binaries:
#    for binp in b_list:
#        if bin[1].endswith("cpython-310-x86_64-linux-gnu.so") or (binp in bin[0] and not binp == "lib"):
#            print(binp, bin)
#            bin_tmp_list.append(bin)
#a.binaries = bin_tmp_list
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

from json import loads
with open("binaries.json") as f:
    bin = loads(f.read())

from os import listdir, remove, rmdir
from os.path import exists
from shutil import rmtree
files = listdir("dist/Fleet")
for file in files:
    if ".so" in file and file not in bin:
        remove(f"dist/Fleet/{file}")
        print(f"removed {file}")
if exists("dist/Fleet/gi_typelibs"):
    rmtree("dist/Fleet/gi_typelibs")
    print("removed 'dist/Fleet/gi_typelibs'")