# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, copy_metadata

project_root = Path(SPECPATH)

datas = [(str(project_root / "data" / "raw"), "data/raw")]
package_src = project_root / "src" / "api_analyse"
for py_file in package_src.rglob("*.py"):
    datas.append((str(py_file), str(py_file.relative_to(project_root / "src").parent)))
binaries = []
hiddenimports = [
    "api_analyse.display.show",
    "typer",
    "click",
    "dotenv",
    "sqlalchemy",
]

for pkg in (
    "streamlit",
    "streamlit_folium",
    "folium",
    "branca",
    "matplotlib",
    "pandas",
    "altair",
    "jsonschema",
):
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
    except Exception:
        hiddenimports.append(pkg)
        continue
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hidden

for pkg in ("streamlit", "streamlit_folium", "folium", "jsonschema"):
    try:
        datas += copy_metadata(pkg)
    except Exception:
        pass

a = Analysis(
    [str(project_root / "src" / "api_analyse" / "__main__.py")],
    pathex=[str(project_root / "src")],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="api-analyse",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="api-analyse",
)
