"""Build the Windows Desktop Edition release end-to-end:

    1. `npm run build` in frontend/ (fresh static assets)
    2. PyInstaller against app.spec (one-folder bundle), output straight
       into desktop_app/release/FIFA-Prediction/
    3. Zip that folder -> desktop_app/release/FIFA-Prediction-win-x64.zip

Both the runnable folder AND the zip end up side by side under
desktop_app/release/ — that whole folder is exactly what to attach to a
GitHub Release (the zip for most users to download; the unpacked folder
if you want to smoke-test the exact bits before uploading, without
re-extracting the zip).

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

RELEASE_DIR = DESKTOP_APP_DIR / "release"
BUNDLE_DIR = RELEASE_DIR / "FIFA-Prediction"
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

    RELEASE_DIR.mkdir(parents=True, exist_ok=True)

    print("[build_release] Running PyInstaller (this can take a few minutes)...")
    # --distpath sends the one-folder bundle straight to release/ instead
    # of PyInstaller's default dist/ — see module docstring for why both
    # outputs live in the same place. --workpath (intermediate build
    # cache, not a deliverable) stays at the default desktop_app/build/.
    run(
        [
            str(PYINSTALLER),
            "app.spec",
            "--noconfirm",
            "--distpath",
            str(RELEASE_DIR),
        ],
        cwd=DESKTOP_APP_DIR,
    )

    if not BUNDLE_DIR.exists():
        print(f"[build_release] Expected {BUNDLE_DIR} to exist after build, but it does not.", file=sys.stderr)
        return 1

    if RELEASE_ZIP.exists():
        RELEASE_ZIP.unlink()

    print(f"[build_release] Zipping {BUNDLE_DIR} -> {RELEASE_ZIP}...")
    archive_base = str(RELEASE_ZIP.with_suffix(""))
    shutil.make_archive(archive_base, "zip", root_dir=BUNDLE_DIR.parent, base_dir=BUNDLE_DIR.name)

    print(f"[build_release] Done.\n  Folder: {BUNDLE_DIR}\n  Zip:    {RELEASE_ZIP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
