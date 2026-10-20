"""Build the Windows Desktop Edition release end-to-end:

    1. `npm run build` in frontend/ (fresh static assets)
    2. PyInstaller against app.spec (one-folder bundle) into
       desktop_app/build/dist/FIFA-Prediction/, plus the project LICENSE
    3. Zip that folder's CONTENTS -> desktop_app/release/FIFA-Prediction-win-x64.zip

The zip has no wrapping folder: it extracts straight to
`FIFA-Prediction.exe`, `_internal/` and `LICENSE`. release/ only ever holds
the zip — that's the file to attach to a GitHub Release. The unpacked
build/dist/FIFA-Prediction/ folder is the same bits, handy for a smoke test
before uploading.

Usage (from anywhere):
    .venv/Scripts/python.exe desktop_app/build_release.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DESKTOP_APP_DIR = PROJECT_ROOT / "desktop_app"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
PYINSTALLER = PROJECT_ROOT / ".venv" / "Scripts" / "pyinstaller.exe"
LICENSE_FILE = PROJECT_ROOT / "LICENSE"

DIST_DIR = DESKTOP_APP_DIR / "build" / "dist"
BUNDLE_DIR = DIST_DIR / "FIFA-Prediction"
RELEASE_DIR = DESKTOP_APP_DIR / "release"
RELEASE_ZIP = RELEASE_DIR / "FIFA-Prediction-win-x64.zip"


def run(command: list[str], cwd: Path) -> None:
    print(f"[build_release] $ {' '.join(command)}  (cwd={cwd})")
    subprocess.run(command, cwd=cwd, check=True)


def main() -> int:
    if not PYINSTALLER.exists():
        print(
            f"[build_release] PyInstaller not found at {PYINSTALLER}.\n"
            "Install it in the project venv first: "
            ".venv/Scripts/python.exe -m pip install pyinstaller",
            file=sys.stderr,
        )
        return 1

    npm = shutil.which("npm")
    if npm is None:
        print("[build_release] npm not found on PATH.", file=sys.stderr)
        return 1

    print("[build_release] Building frontend...")
    run([npm, "run", "build"], cwd=FRONTEND_DIR)

    print("[build_release] Running PyInstaller (this can take a few minutes)...")
    run(
        [str(PYINSTALLER), "app.spec", "--noconfirm", "--distpath", str(DIST_DIR)],
        cwd=DESKTOP_APP_DIR,
    )
    shutil.copy2(LICENSE_FILE, BUNDLE_DIR / "LICENSE")

    # release/ is fully generated — clear anything from earlier builds
    # (including the old layout's unpacked folder) so it only holds the zip.
    if RELEASE_DIR.exists():
        shutil.rmtree(RELEASE_DIR)
    RELEASE_DIR.mkdir(parents=True)

    print(f"[build_release] Zipping {BUNDLE_DIR} -> {RELEASE_ZIP}...")
    shutil.make_archive(str(RELEASE_ZIP.with_suffix("")), "zip", root_dir=BUNDLE_DIR)

    print(f"[build_release] Done.\n  Zip:      {RELEASE_ZIP}\n  Unpacked: {BUNDLE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
