# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\plot\\main.py'],
    pathex=[],
    binaries=[('.\\mainWidget.cp313-win_amd64.pyd', '.'), ('.\\mainGUI.cp313-win_amd64.pyd', '.'), 
    ('.\\metadatatable.cp313-win_amd64.pyd', '.'), ('.\\mdxreader.cp313-win_amd64.pyd', '.')],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'tkinter', 'PyQt6', 'torch', 'pillow', 'IPython', 'numba', 'jupyter_client', 'jupyter_code', 'jupyterlab_widgets'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='egrliono',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)
