# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

spec_dir = os.path.dirname(os.path.abspath(SPEC))
# When spec is in desktop/, repo_root is one level up
if os.path.basename(spec_dir) == 'desktop':
    desktop_dir = spec_dir
    repo_root = os.path.dirname(spec_dir)
else:
    repo_root = spec_dir
    desktop_dir = os.path.join(repo_root, 'desktop')

entrypoint = os.path.join(repo_root, 'packaging', 'autofailover_entry.py')

datas = [
    (os.path.join(desktop_dir, 'assets'), 'desktop/assets'),
    (os.path.join(desktop_dir, 'VERSION'), 'desktop'),
]

if os.path.exists(os.path.join(repo_root, 'assets')):
    datas.append((os.path.join(repo_root, 'assets'), 'assets'))

try:
    datas += collect_data_files('customtkinter')
except Exception:
    pass

hiddenimports = [
    'PIL',
    'PIL.Image',
    'desktop',
    'desktop.resources',
    'desktop.models',
    'desktop.models.interface',
    'desktop.models.metrics',
    'desktop.models.policy',
    'desktop.models.telemetry',
    'desktop.models.events',
    'desktop.core',
    'desktop.core.events.bus',
    'desktop.core.failover.orchestrator',
    'desktop.core.health.evaluator',
    'desktop.core.policy.engine',
    'desktop.core.probe.rfc3550',
    'desktop.core.recovery.arbiter',
    'desktop.core.speedtest.runner',
    'desktop.core.telemetry.sampler',
    'desktop.core.workload.watcher',
    'desktop.platform',
    'desktop.platform.base',
    'desktop.platform.linux.backend',
    'desktop.platform.windows.backend',
    'desktop.platform.macos.backend',
    'desktop.ui',
    'desktop.ui.theme',
    'desktop.ui.app',
    'desktop.ui.splash.screen',
    'desktop.ui.dashboard.cockpit',
]

try:
    hiddenimports += collect_submodules('customtkinter')
except Exception:
    pass

a = Analysis(
    [entrypoint],
    pathex=[repo_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
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
    [],
    exclude_binaries=True,
    name='AutoFailover 3.0',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # console=True allows diagnostic logging and CLI flags like --headless, --version, --self-test
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
    upx=False,
    upx_exclude=[],
    name='AutoFailover 3.0',
)

# On macOS, build App bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='AutoFailover 3.0.app',
        icon=None,
        bundle_identifier='com.modula.autofailover',
    )
