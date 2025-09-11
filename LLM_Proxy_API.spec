# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('config.yaml', 'config.yaml'), ('logs', 'logs'), ('templates', 'templates'), ('static', 'static')]
binaries = []
hiddenimports = ['uvicorn', 'fastapi', 'flask', 'src', 'src.core', 'src.core.config', 'src.core.logging', 'src.core.app_config', 'src.core.auth', 'src.core.app_state', 'src.api', 'src.api.endpoints', 'src.models', 'src.models.requests', 'src.providers', 'src.providers.base', 'src.providers.openai', 'src.providers.anthropic', 'src.services', 'src.services.provider_loader']
tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['main_dynamic.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LLM_Proxy_API',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
