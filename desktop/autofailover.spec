# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

base_dir = os.path.dirname(os.path.abspath(SPEC))

datas = [
    (os.path.join(base_dir, 'assets'), 'desktop/assets'),
    (os.path.join(base_dir, 'VERSION'), 'desktop'),
]

try:
    datas += collect_data_files('customtkinter')
except Exception:
    pass

hiddenimports = [
    'PIL',
    'PIL.Image',
    'desktop',
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
    [os.path.join(base_dir, 'main.py')],
    pathex=[os.path.dirname(base_dir)],
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
    console=True,  # console=True allows diagnostic logging and CLI flags like --headless
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
