# PyInstaller spec — produces a single-file executable for the BIOS sim.
#
# Build:
#   Windows: pyinstaller bios.spec        -> dist/bios.exe
#   Linux:   pyinstaller bios.spec        -> dist/bios
#   macOS:   pyinstaller bios.spec        -> dist/bios
#
# The spec is OS-agnostic. PyInstaller produces a binary native to the
# host OS — there is no cross-compile. To produce bios.exe from Linux,
# either install Wine + a Windows Python, or rely on the GitHub Actions
# workflow at .github/workflows/build.yml.

# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files


block_cipher = None


# Bundle the entire assets/ tree (fonts + reference images).
# Reference images are not strictly required at runtime, but bundling
# them keeps the build self-contained and they are small.
datas = [
    ("assets/fonts/PxPlus_IBM_VGA_8x16.ttf", "assets/fonts"),
    ("assets/fonts/Px437_IBM_VGA_8x16.ttf", "assets/fonts"),
]


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "vendors.ami",
        "vendors.award",
        "vendors.efi",
        "shell",
        "audio",
        "procedural",
        "shifts",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Trim down: PyInstaller pulls many optional deps by default.
        "tkinter",
        "unittest",
        "test",
        "distutils",
    ],
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
    name="bios",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,                       # no console window on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=None,                         # set e.g. "assets/icon.ico" if added
)
