# FIFA Prediction — Desktop Edition

A single Python process: the shared FastAPI backend (`backend/app/main.py`,
the exact same app the Web edition runs) serving both its API and the
built Vue frontend, shown in a native window via
[pywebview](https://pywebview.flowrl.com/) (WebView2 on Windows — no
Chromium bundled, it uses the runtime already installed on Windows 10/11).

See `main.py`'s module docstring for the full architecture rationale and
why this replaced an earlier Electron-based design.

## Requirements to build

```bash
.venv/Scripts/pip install -r backend/requirements.txt -r desktop_app/requirements.txt
```

Also needs Node.js, only to build the frontend — not needed at runtime by
the packaged app.

## Run in dev (no packaging)

```bash
.venv/Scripts/python.exe desktop_app/main.py
```

Uses `frontend/dist/` if it already exists (run `npm run build` in
`frontend/` first), and the real `datasets/builtin/results.csv` +
`models/decision_tree/v1/` from the project tree directly — no bundling
needed to iterate.

## Build the release zip

```bash
.venv/Scripts/python.exe desktop_app/build_release.py
```

This builds the frontend, runs PyInstaller against `app.spec`, and writes
`desktop_app/release/FIFA-Prediction-win-x64.zip` — the only file in
`release/`, and the one to attach to a GitHub Release. The zip has no
wrapping folder: it extracts straight to `FIFA-Prediction.exe`,
`FIFA-Prediction.exe.config`, `_internal\` and `LICENSE`. The same bundle, unzipped, is left at
`desktop_app/build/dist/FIFA-Prediction/` for a quick smoke test.

Why a folder and not a single exe: a PyInstaller one-file exe re-extracts
its ~190 MB runtime into `%TEMP%` on every launch (measured: 23–26 s per
start vs. ~4 s for the folder build, plus leftovers on the system drive if
it crashes).

### Startup sequence

The window opens immediately on a built-in loading screen and the backend
boots on a background thread (`_boot_backend` in `main.py`); the UI loads
as soon as `/api/health` answers. The backend prefers port 17872 and falls
back to any free port if that one is taken.

First launch of a freshly built (or freshly downloaded) executable is
often noticeably slower than later launches — Windows Defender/SmartScreen
scans a new, unsigned binary and its ~500 bundled DLL files the first time
each one is touched, and remembers the verdict after that. This is normal
and not a bug; if you see a "Windows protected your PC" SmartScreen
prompt, click **More info → Run anyway**.

## Application data location

Fully portable by default: all user data lives right next to the exe, so
moving or deleting that one folder leaves nothing behind anywhere else on
the system.

```
<extracted folder>\
├── FIFA-Prediction.exe
├── FIFA-Prediction.exe.config   # see Troubleshooting
├── _internal\...
├── LICENSE
└── data\
    ├── app.db              # SQLite database (datasets/models/predictions metadata)
    ├── datasets\user\       # uploaded dataset versions
    ├── models\              # trained model artifacts
    ├── webview2\            # WebView2's browser profile/cache (kept between launches for faster startup)
    ├── logs\app.log         # startup + runtime log — check this first if something goes wrong
    └── .instance-lock       # OS-level exclusive lock (see main.py) preventing a second launch
```

If that folder somehow isn't writable (e.g. installed under
`Program Files` without admin rights), it falls back to
`%APPDATA%\FIFA-Prediction\` instead — but this is only a fallback, never
the default.

The log folder can be moved elsewhere via **Settings → Change log
folder…** in the app itself (native folder picker), applied immediately
without restarting.

## Troubleshooting

- **"FIFA Prediction is already running"**: another instance holds the
  single-instance lock. Check the taskbar for the existing window; if you
  don't see one but still get this message, a previous run may not have
  exited cleanly — check Task Manager for a leftover `FIFA-Prediction.exe`.
- **"Backend failed to start" / unexpected error dialogs**: the exact
  exception is written to `logs\app.log` (see above) — check there first.
- **Slow first launch**: see the SmartScreen note above.
- **"Failed to resolve Python.Runtime.Loader.Initialize"**: the
  `FIFA-Prediction.exe.config` next to the exe is missing. A zip downloaded
  from the internet and extracted with Explorer marks every file as "from
  the internet", and .NET Framework refuses to load the bundled DLLs unless
  that config (`loadFromRemoteSources`) is present. Re-extract the full zip,
  or right-click the zip → Properties → **Unblock** before extracting.

## Known constraints

- Windows only for now (pywebview also supports macOS/Linux, but the
  packaging step — `app.spec` — is Windows-specific; porting it is future
  work, not started here).
- Requires the WebView2 Runtime, which ships with Windows 11 and is
  auto-installed via Windows Update on Windows 10 (version 1803+). Nearly
  every Windows 10/11 machine already has it; pywebview will show a clear
  error if it's genuinely missing rather than failing silently.
