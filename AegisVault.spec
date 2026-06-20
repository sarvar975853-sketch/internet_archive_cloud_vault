# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

# SPECPATH is set by PyInstaller to the directory containing this .spec file
_spec_dir = SPECPATH
_parent_dir = os.path.dirname(_spec_dir)

a = Analysis(
    [os.path.join(_spec_dir, 'main.py')],
    pathex=[_parent_dir, _spec_dir],
    binaries=[],
    datas=[
        (os.path.join(_spec_dir, 'assets', 'icon.png'), 'assets'),
        (os.path.join(_spec_dir, 'gui', 'assets', 'cloud_hero.png'), 'gui/assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'cryptography',
        'cryptography.hazmat.primitives.ciphers',
        'cryptography.hazmat.primitives.kdf.pbkdf2',
        'cryptography.hazmat.primitives.kdf.scrypt',
        'requests',
        'internetarchive',
        'aegis_vault',
        'aegis_vault.core',
        'aegis_vault.core.credentials',
        'aegis_vault.core.crypto',
        'aegis_vault.core.storage',
        'aegis_vault.core.queue_worker',
        'aegis_vault.core.url_downloader',
        'aegis_vault.gui',
        'aegis_vault.gui.app',
        'aegis_vault.gui.theme',
        'aegis_vault.gui.login',
        'aegis_vault.gui.dashboard',
        'aegis_vault.gui.sidebar',
        'aegis_vault.gui.upload',
        'aegis_vault.gui.url_upload',
        'aegis_vault.gui.explorer',
        'aegis_vault.gui.files',
        'aegis_vault.gui.settings',
        'aegis_vault.gui.toast',
        'aegis_vault.utils',
        'aegis_vault.utils.logger',
        'version',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinterdnd2'],
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
    name='AegisVault',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(_spec_dir, 'assets', 'icon.icns'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AegisVault',
)

app = BUNDLE(
    coll,
    name='Aegis Vault.app',
    icon=os.path.join(_spec_dir, 'assets', 'icon.icns'),
    bundle_identifier='com.aegisvault.app',
    info_plist={
        'CFBundleDisplayName': 'Aegis Vault',
        'CFBundleShortVersionString': '2.0.0',
        'CFBundleVersion': '2.0.0',
        'NSHighResolutionCapable': True,
        'NSRequiresAquaSystemAppearance': False,
        'LSMinimumSystemVersion': '10.15',
        'CFBundleName': 'Aegis Vault',
        'CFBundleIdentifier': 'com.aegisvault.app',
    },
)
