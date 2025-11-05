# build_exe.py - Build standalone executable for Windows (FIXED scipy/pydoc issue)
import os
import sys
from pathlib import Path

import PyInstaller.__main__


def build():
    """Build Jarvis as a standalone executable"""

    print("🔨 Building Jarvis Assistant...")
    print("📊 Target: MSI Thin 15 B13UC (16GB RAM, RTX 3050)")
    print()

    # Project root
    root = Path(__file__).parent

    # Icon (create if doesn't exist)
    icon_path = root / "assets" / "jarvis.ico"
    if not icon_path.exists():
        print("⚠️  No icon found, using default")
        icon_arg = []
    else:
        icon_arg = [f"--icon={icon_path}"]

    # Data files to include
    data_files = [
        (root / "custom_apps.json", ".") if (root / "custom_apps.json").exists() else None,
        (root / ".env", ".") if (root / ".env").exists() else None,
        (root / "venv/Lib/site-packages/openwakeword/resources", "openwakeword/resources"),
    ]

    # Filter out None values
    data_files = [f for f in data_files if f is not None]

    datas = []
    for src, dst in data_files:
        if src.exists():
            datas.extend(["--add-data", f"{src}{os.pathsep}{dst}"])
            print(f"✓ Including: {src.name}")

    print()

    # Hidden imports (for dynamic imports) - ADDED: pydoc, scipy, sklearn
    hidden_imports = [
        # Core
        "pyttsx3.drivers",
        "pyttsx3.drivers.sapi5",
        "win32com.client",
        "win32gui",
        "win32con",
        "win32process",
        "psutil",
        "spacy",
        "whisper",
        "torch",
        "playwright",
        "elevenlabs",
        "gtts",
        "openwakeword",
        # ML/Data processing (needed for predictive_model.py)
        "sklearn",
        "sklearn.feature_extraction",
        "sklearn.feature_extraction.text",
        "sklearn.linear_model",
        "sklearn.pipeline",
        "scipy",
        "scipy.sparse",
        "pandas",
        "numpy",
        # Standard library (fix for pydoc issue)
        "pydoc",
        "doctest",
        "inspect",
        # Async/networking
        "aiohttp",
        # UI/Input
        "customtkinter",
        "sounddevice",
        "pyautogui",
        "keyboard",
        "pynput",
        # Web/Database
        "sqlite3",
        "json",
        "urllib",
        "urllib.request",
    ]

    hidden_args = []
    for imp in hidden_imports:
        hidden_args.extend(["--hidden-import", imp])

    # Excluded modules (to reduce build size and avoid issues)
    excluded_modules = [
        "matplotlib",
        "tensorflow",
        "IPython",
        "pytest",
        "unittest",
        "webrtcvad",  # Exclude to avoid hook issues
    ]

    exclude_args = []
    torch_excludes = [
        "torch.cuda",
        "torch.distributed",
        "torch.distributions",
        "torch.fx",
        "torch.jit",
        "torch.linalg",
        "torch.quantization",
        "torch.sparse",
        "torch.special",
        "torch.testing",
        "torch.utils.data",
        "torch.utils.tensorboard",
        "torch._C",
        "torchvision",
        "torchaudio",
    ]
    for mod in torch_excludes:
        exclude_args.extend(["--exclude-module", mod])
    sklearn_excludes = [
        "sklearn.datasets",
        "sklearn.cluster",
        "sklearn.decomposition",
        "sklearn.ensemble",
        "sklearn.metrics",
        "sklearn.model_selection",
        "sklearn.preprocessing",
        "sklearn.svm",
        "sklearn.tree",
    ]
    for mod in sklearn_excludes:
        exclude_args.extend(["--exclude-module", mod])
    cv2_excludes = [
        "cv2.cv2",
        "cv2.data",
        "cv2.gapi",
        "cv2.mat_wrapper",
        "cv2.utils",
        "cv2.videoio",
    ]
    for mod in cv2_excludes:
        exclude_args.extend(["--exclude-module", mod])
    misc_excludes = [
        "matplotlib",
        "seaborn",
        "plotly",
        "bokeh",
        "jinja2",
        "markupsafe",
        "werkzeug",
        "flask",
        "pytest",
        "_pytest",
        "py",
        "pluggy",
        "IPython",
        "ipykernel",
        "jupyter_client",
        "tornado",
        "zmq",
        "sqlite3.dump",
        "pydoc_data",
    ]
    for mod in misc_excludes:
        exclude_args.extend(["--exclude-module", mod])
    # ----- ADD THESE 6 LINES -----
    more_excludes = [
        "matplotlib",
        "PIL.PngImagePlugin",
        "PIL.JpegImagePlugin",
        "scipy.optimize",
        "sklearn.datasets",
        "sklearn.cluster",
        "tensorflow",
        "torchvision",
        "IPython",
        "jupyter",
        "pytest",
        "unittest",
        "doctest",
        "pydoc",
        "inspect",
        "cv2",
        "PyQt5",
        "PySide2",
        "PySide6",
        "tkinter",
    ]
    for mod in more_excludes:
        exclude_args.extend(["--exclude-module", mod])
    for exc in excluded_modules:
        exclude_args.extend(["--exclude-module", exc])

    # PyInstaller arguments
    args = [
        "main_standalone.py",
        "--name=Jarvis",
        "--onefile",
        "--windowed",  # No console window
        "--clean",
        *icon_arg,
        *datas,
        *hidden_args,
        *exclude_args,
        "--optimize=2",
        "--noupx",  # Disable UPX (better compatibility)
        "--noconfirm",
        # Collect submodules
        "--collect-submodules=torch",
        "--collect-submodules=whisper",
        "--collect-submodules=openwakeword",
        "--collect-submodules=sklearn",
        "--collect-submodules=scipy",
        "--collect-submodules=spacy",
    ]

    print("📦 PyInstaller Configuration:")
    print("  • Mode: Onefile (single executable)")
    print("  • Window: Windowed (no console)")
    print("  • Optimization: Level 2")
    print(f"  • Icon: {'Yes' if icon_arg else 'Default'}")
    print(f"  • Data files: {len(data_files)} included")
    print(f"  • Hidden imports: {len(hidden_imports)} included")
    print(f"  • Excluded modules: {len(excluded_modules)} excluded")
    print()

    print("🔄 Building... (this may take 10-15 minutes)")
    print("   - First build is slower (compiling dependencies)")
    print("   - Subsequent builds will be faster")
    print()

    try:
        PyInstaller.__main__.run(args)

        # Check if build was successful
        exe_path = root / "dist" / "Jarvis.exe"
        if exe_path.exists():
            file_size_mb = exe_path.stat().st_size / (1024**2)

            print()
            print("=" * 60)
            print("✅ BUILD SUCCESSFUL!")
            print("=" * 60)
            print()
            print(f"📁 Executable: {exe_path}")
            print(f"📊 Size: {file_size_mb:.1f}MB")
            print()
            print("📝 NEXT STEPS:")
            print()
            print("1. Copy these files to same folder as Jarvis.exe:")
            print("   - .env (with your API keys)")
            print("   - custom_apps.json (optional)")
            print()
            print("2. Test the executable:")
            print(f"   {exe_path}")
            print()
            print("3. Create a shortcut:")
            print("   - Right-click Jarvis.exe")
            print("   - Select 'Create shortcut'")
            print()
            print("4. (Optional) Auto-start on boot:")
            print("   - Move shortcut to:")
            print(
                "   - C:\\Users\\YourName\\AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup"
            )
            print()
            print("5. Distribute to others:")
            print("   - Zip the dist/ folder")
            print("   - Share with Jarvis.exe, .env, and custom_apps.json")
            print()
            print("=" * 60)
            print()
            return True

        else:
            print()
            print("❌ Build completed but executable not found!")
            print("   Check the build output above for errors.")
            return False

    except Exception as e:
        print()
        print("=" * 60)
        print("❌ BUILD FAILED!")
        print("=" * 60)
        print()
        print(f"Error: {e}")
        print()
        print("TROUBLESHOOTING:")
        print()
        print("1. Missing dependencies:")
        print("   pip install -r requirements.txt --upgrade")
        print()
        print("2. Clear PyInstaller cache:")
        print("   rmdir /s /q build")
        print("   rmdir /s /q dist")
        print()
        print("3. Rebuild:")
        print("   python build_exe.py")
        print()
        return False


if __name__ == "__main__":
    success = build()

    sys.exit(0 if success else 1)
