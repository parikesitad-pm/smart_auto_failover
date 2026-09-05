import os
import subprocess
import sys


def build_standalone():
    """
    Build standalone Windows executable (.exe) using PyInstaller
    with Windows Administrator manifest embedded.
    """
    print("=" * 70)
    print(" Building Smart Auto-Failover Network Monitor Standalone (.exe)")
    print("=" * 70)

    # Check if pyinstaller is installed
    try:
        import PyInstaller
        print(f"PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("PyInstaller not found. Installing pyinstaller via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onedir",  # onedir is faster to launch than onefile
        "--windowed",  # No console window
        "--uac-admin",  # Embed UAC Administrator execution manifest
        "--name", "SmartAutoFailover",
        "--collect-all", "customtkinter",
        "--collect-all", "darkdetect",
        main_py,
    ]

    print(f"\nRunning command:\n{' '.join(cmd)}\n")
    ret = subprocess.call(cmd, cwd=script_dir)
    if ret == 0:
        dist_path = os.path.join(script_dir, "dist", "SmartAutoFailover", "SmartAutoFailover.exe")
        print("\n" + "=" * 70)
        print("BUILD SUCCESSFUL!")
        print(f"Executable created at:\n  {dist_path}")
        print("=" * 70)
    else:
        print(f"\nBuild failed with exit code: {ret}")


if __name__ == "__main__":
    build_standalone()

