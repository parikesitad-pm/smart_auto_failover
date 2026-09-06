"""
MODULA - Smart Auto Failover v2.3
Windows Release Packaging Script
Produces: dist_app/MODULA-v2.3-windows-x64.zip and dist_app/MODULA/MODULA.exe
"""
import os
import shutil
import subprocess
import sys
import zipfile

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

VERSION = "v2.3"
ARCH = "windows-x64"
BUNDLE_NAME = f"MODULA-{VERSION}-{ARCH}"


def build():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    dist_dir = os.path.join(script_dir, "dist_app")
    build_dir = os.path.join(script_dir, "build")
    assets_src = os.path.join(script_dir, "assets")
    ico_file = os.path.join(assets_src, "modula.ico")
    main_py = os.path.join(script_dir, "main.py")

    print("=" * 70)
    print(f"[+] BUILDING MODULA {VERSION} BUNDLE FOR WINDOWS ({ARCH})")
    print("=" * 70)

    # 1. Verify PyInstaller
    try:
        import PyInstaller
        print(f"[*] PyInstaller version: {PyInstaller.__version__}")
    except ImportError:
        print("[!] PyInstaller not found. Installing via pip...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

    dist_staging = os.path.join(build_dir, "dist_staging")
    os.makedirs(dist_staging, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    # 2. Build onedir application with PyInstaller to staging directory
    print("\n[*] Compiling standalone application binary with PyInstaller...")
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--windowed",
        "--uac-admin",
        "--distpath", dist_staging,
        "--workpath", os.path.join(build_dir, "pyi_work"),
        "--name", "MODULA",
        "--icon", ico_file,
        "--add-data", f"{assets_src};assets",
        "--collect-all", "customtkinter",
        "--collect-all", "darkdetect",
        "--collect-all", "PIL",
        main_py,
    ]

    ret = subprocess.call(cmd, cwd=script_dir)
    if ret != 0:
        print(f"[x] PyInstaller failed with exit code {ret}")
        sys.exit(ret)

    app_folder = os.path.join(dist_staging, "MODULA")
    if not os.path.isdir(app_folder):
        print(f"[x] Target folder not found: {app_folder}")
        sys.exit(1)

    # 3. Copy launcher batch script and documentation into staging app
    run_bat = os.path.join(script_dir, "run_admin.bat")
    if os.path.exists(run_bat):
        shutil.copy2(run_bat, os.path.join(app_folder, "run_admin.bat"))

    readme_src = os.path.join(script_dir, "README.md")
    if os.path.exists(readme_src):
        shutil.copy2(readme_src, os.path.join(app_folder, "README.md"))

    # Also place a version file
    with open(os.path.join(app_folder, "VERSION.txt"), "w", encoding="utf-8") as vf:
        vf.write(f"MODULA - Smart Auto Failover\nVersion: {VERSION}\nPlatform: Windows x64\nAuthor: parikesitad-pm\n")

    # 4. Create ZIP distribution bundle
    zip_filename = f"{BUNDLE_NAME}.zip"
    zip_filepath = os.path.join(dist_dir, zip_filename)
    print(f"\n[*] Packaging ZIP archive: {zip_filepath}...")

    with zipfile.ZipFile(zip_filepath, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(app_folder):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, dist_staging)
                zf.write(full_path, rel_path)

    # 5. Try syncing into dist_app/MODULA if not locked by active process
    dest_modula = os.path.join(dist_dir, "MODULA")
    try:
        shutil.copytree(app_folder, dest_modula, dirs_exist_ok=True)
        print(f"[+] Updated local folder: {dest_modula}")
    except Exception:
        print(f"[!] Note: dist_app/MODULA is currently in-use by running app. Standalone ZIP package generated cleanly.")

    zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)

    print("\n" + "=" * 70)
    print("[SUCCESS] WINDOWS BUILD & PACKAGING COMPLETE!")
    print("=" * 70)
    print(f"[ZIP Package] : {zip_filepath} ({zip_size_mb:.2f} MB)")
    print(f"[Folder App]  : {app_folder}")
    print(f"[Executable]  : {os.path.join(app_folder, 'MODULA.exe')}")
    print("=" * 70)


if __name__ == "__main__":
    build()
