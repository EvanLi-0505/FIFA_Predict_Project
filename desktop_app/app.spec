# -*- mode: python ; coding: utf-8 -*-
#
# Builds the Windows Desktop Edition as a one-folder PyInstaller bundle
# (--onedir: startup would otherwise pay a multi-second self-extraction
# cost on every launch for a pandas/scikit-learn-sized bundle — see
# run_server.spec's retired equivalent note, same reasoning applies here).
#
# Run from the `desktop_app/` directory:
#   ../.venv/Scripts/pyinstaller.exe app.spec --noconfirm
# or use build_release.py, which also builds the frontend first and zips
# the result.
#
# This replaces the earlier Electron + separately-bundled-FastAPI-backend
# architecture: `desktop_app/main.py` is a single process that runs the
# SAME FastAPI app (imported from `backend.app.main`) in a background
# thread and shows it in a pywebview (WebView2) window — see main.py's
# module docstring for the full rationale.

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

PROJECT_ROOT = Path(SPECPATH).resolve().parent

datas = []
binaries = []
hiddenimports = []

# collect_all() is used (rather than relying on PyInstaller's automatic
# import analysis) for the libraries most notorious for hidden/dynamic
# imports that static analysis misses: scikit-learn (Cython extension
# submodules), pandas (C extensions + a large plugin surface), uvicorn
# (protocol/loop implementations selected at runtime), fastapi/pydantic
# (dynamic model machinery), pywebview/pythonnet/clr_loader (the WebView2
# GUI backend is loaded dynamically at runtime, not via a static import
# analysis can follow), and pymysql (the Web edition's MySQL driver —
# unused at runtime by the Desktop build, but harmless to include and
# keeps `core`/`database` importable without a Desktop-specific fork).
for package in (
    "sklearn",
    "pandas",
    "uvicorn",
    "fastapi",
    "pydantic",
    "pymysql",
    "webview",
    "clr_loader",
    "pythonnet",
):
    pkg_datas, pkg_binaries, pkg_hiddenimports = collect_all(package)
    datas += pkg_datas
    binaries += pkg_binaries
    hiddenimports += pkg_hiddenimports

# Same reasoning as run_server.spec: collect_all() also pulls in each
# package's own internal test suite (thousands of extra modules for
# scikit-learn alone) — filtered out here since nothing in this app
# imports a `*.tests` module.
hiddenimports = [
    name for name in hiddenimports if ".tests." not in name and not name.endswith(".tests")
]
datas = [d for d in datas if "tests" not in d[1].split("\\") and "tests" not in d[1].split("/")]

# Bundled read-only resources, resolved at runtime via
# `desktop_app.main.resource_root()` (PyInstaller sets `sys._MEIPASS` to
# wherever these land, i.e. `<dist>/FIFA-Prediction/_internal/`).
datas += [
    (str(PROJECT_ROOT / "datasets" / "builtin" / "results.csv"), "datasets/builtin"),
    (str(PROJECT_ROOT / "models" / "decision_tree" / "v1"), "models/decision_tree/v1"),
    (str(PROJECT_ROOT / "models" / "logistic_regression" / "elo_v1"), "models/logistic_regression/elo_v1"),
    # Vite's dist/ contents are flattened one level (no "dist" folder in
    # the bundle) — see main.py's frontend_dist_dir() for why.
    (str(PROJECT_ROOT / "frontend" / "dist"), "frontend"),
]

a = Analysis(
    ["main.py"],
    pathex=[str(PROJECT_ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Not imported anywhere in core/backend/database/desktop_app (verified
    # before this spec was written) — these only appear in the standalone
    # notebook scripts, which are not part of the bundled app.
    excludes=["matplotlib", "seaborn", "IPython", "jupyter", "notebook"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FIFA-Prediction",
    # NOT under desktop_app/build/ — that's PyInstaller's own intermediate
    # working directory (--workpath), wiped on every clean rebuild.
    icon=str(PROJECT_ROOT / "desktop_app" / "icon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # console=False: this IS the user-facing app (unlike the retired
    # run_server.exe, nothing pipes its stdout elsewhere) — a console
    # window behind the WebView2 window would look broken. All logging
    # goes to <exe_dir>/data/logs/app.log instead (see main.py's
    # setup_logging/app_data_dir) and to a MessageBox for fatal startup
    # errors (see main.py's show_native_error).
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FIFA-Prediction",
)
