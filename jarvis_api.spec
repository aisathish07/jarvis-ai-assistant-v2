# -*- mode: python ; coding: utf-8 -*-

import sys
import os

# Get the path to the root of the project
block_cipher = None

# The main script
a = Analysis(
    ['jarvis_api_bridge.py'],
    pathex=[os.getcwd()],  # Add project root to path
    binaries=[],
    datas=[
        ('skills', 'skills')  # Bundle the skills directory
    ],
    hiddenimports=[
        'jarvis_core_optimized',
        'jarvis_skills',
        'jarvis_plugin_hotreload',
        'jarvis_config',
        'model_router',
        'skill_bus',
        # Add other necessary modules here
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
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
    name='JARVIS_API',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False for a windowless app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
