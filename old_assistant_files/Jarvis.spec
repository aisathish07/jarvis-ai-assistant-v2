# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

hiddenimports = ['pyttsx3.drivers', 'pyttsx3.drivers.sapi5', 'win32com.client', 'win32gui', 'win32con', 'win32process', 'psutil', 'spacy', 'whisper', 'torch', 'playwright', 'elevenlabs', 'gtts', 'openwakeword', 'sklearn', 'sklearn.feature_extraction', 'sklearn.feature_extraction.text', 'sklearn.linear_model', 'sklearn.pipeline', 'scipy', 'scipy.sparse', 'pandas', 'numpy', 'pydoc', 'doctest', 'inspect', 'aiohttp', 'customtkinter', 'sounddevice', 'pyautogui', 'keyboard', 'pynput', 'sqlite3', 'json', 'urllib', 'urllib.request']
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('whisper')
hiddenimports += collect_submodules('openwakeword')
hiddenimports += collect_submodules('sklearn')
hiddenimports += collect_submodules('scipy')
hiddenimports += collect_submodules('spacy')


a = Analysis(
    ['main_standalone.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Users\\h0093\\Documents\\MY-Assistant\\.env', '.'), ('C:\\Users\\h0093\\Documents\\MY-Assistant\\venv\\Lib\\site-packages\\openwakeword\\resources', 'openwakeword/resources')],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'IPython', 'pytest', 'unittest', 'webrtcvad'],
    noarchive=False,
    optimize=2,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [('O', None, 'OPTION'), ('O', None, 'OPTION')],
    name='Jarvis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
