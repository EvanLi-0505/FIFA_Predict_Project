"""Windows Desktop Edition entry point — single Python process, no Electron.

Architecture (replaces the earlier Electron + PyInstaller-backend + NSIS
installer approach, which was scrapped after Stage 5 QA turned up repeated
cross-process startup races — see git history on `desktop/` for the
retired implementation):

    pywebview window  <--http://127.0.0.1:PORT-->  FastAPI (same process,
                                                     background thread)

`backend.app.main.app` — the EXACT SAME FastAPI app the Web edition runs —
is imported as-is and reused unmodified; this file only adds two things on
top of it, both desktop-only concerns that must never leak into
`backend/app/main.py` (which the Web edition also imports):

  1. Environment variables pointing the shared `core`/`database` code at
     desktop-appropriate paths (SQLite under the app's own portable data
     folder, the built-in dataset/model bundled next to this executable)
     — set BEFORE importing `backend.app.main`, since
     `backend/app/config.py` reads them at import time.
  2. Serving the built Vue frontend as static files from the SAME FastAPI
     instance, so the desktop window and the API are same-origin (no CORS,
     no `file://` base-path issues — see frontend/vite.config.js's old
     `mode === 'desktop'` branch, no longer needed for this reason and
     removed).

Being one process eliminates essentially every failure mode the Electron
version fought: no child-process spawn/kill dance, no "which process is
actually listening on this port" ambiguity, no separate renderer needing
to learn the backend's address. The only thing still worth guarding
against is the user launching the exe twice — handled below with a plain
OS-level exclusive file lock (released automatically if the process dies,
even via Task Manager — no PID bookkeeping required).

Portability: by explicit request, this app must leave NO trace anywhere
on the system once its extracted folder is deleted. That rules out
%APPDATA% as the default for anything — see `app_data_dir()` (the SQLite
DB / uploaded datasets / trained models / logs) and `_run()`'s
`storage_path` (WebView2's own cookie/cache profile, which pywebview would
otherwise also put under %APPDATA% by default). Both default to living
inside the app's own folder instead, with %APPDATA% only as a last-resort
fallback if that folder genuinely isn't writable.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
import threading
import time
from pathlib import Path

# See SetLogFolderRequest's docstring below for why this must be a
# top-level (not function-local) import.
from pydantic import BaseModel

# Make `backend`, `core`, `database` importable regardless of the current
# working directory this was launched from. In a frozen (PyInstaller)
# build, `app.spec` puts them on `sys.path` directly instead (see
# `pathex`), so this insert is a harmless no-op there — `sys.frozen` guards
# it purely to avoid touching sys.path when it isn't needed.
if not getattr(sys, "frozen", False):
    _project_root = Path(__file__).resolve().parent.parent
    if str(_project_root) not in sys.path:
        sys.path.insert(0, str(_project_root))

logger = logging.getLogger("desktop_app")


def exe_dir() -> Path:
    """Directory containing the actual FIFA-Prediction.exe (or, in dev,
    the project root). NOT the same as `resource_root()`, which points
    inside PyInstaller's `_internal/` subfolder — user data lives as a
    SIBLING of `_internal/`, next to the exe itself, so the whole portable
    folder (exe + data together) can be deleted as one unit with nothing
    left behind anywhere else.
    """

    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def resource_root() -> Path:
    """Directory containing bundled read-only resources (datasets/, models/,
    frontend/dist/). PyInstaller (onedir) unpacks these under `_internal/`
    next to the executable and exposes that path via `sys._MEIPASS`; in dev
    (not frozen), it's just the project root two levels up.
    """

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass is not None:
        return Path(meipass)
    return Path(__file__).resolve().parent.parent


def _is_writable(directory: Path) -> bool:
    try:
        directory.mkdir(parents=True, exist_ok=True)
        probe = directory / ".write_test"
        probe.write_text("", encoding="utf-8")
        probe.unlink()
        return True
    except OSError:
        return False


def app_data_dir() -> Path:
    """Writable directory for the SQLite DB, uploaded datasets, trained
    models, and (by default) logs.

    Defaults to `<exe_dir>/data/` — portable and fully self-contained, per
    explicit user request that nothing be left on the system once this
    folder is deleted. Falls back to `%APPDATA%/FIFA-Prediction/` only if
    that default genuinely isn't writable (e.g. extracted somewhere
    read-only) — refusing to start at all would be worse.
    """

    portable_dir = exe_dir() / "data"
    if _is_writable(portable_dir):
        return portable_dir

    base = os.environ.get("APPDATA") or str(Path.home())
    fallback_dir = Path(base) / "FIFA-Prediction"
    fallback_dir.mkdir(parents=True, exist_ok=True)
    return fallback_dir


def acquire_single_instance_lock(lock_path: Path):
    """Return an open file handle holding an exclusive OS-level lock, or
    None if another instance already holds it. The lock is released
    automatically when this process exits for ANY reason (clean exit,
    crash, or being killed) — no stale-lock cleanup logic needed, unlike a
    plain "lockfile exists" check.
    """

    lock_path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(lock_path, "w")  # noqa: SIM115 - intentionally kept open for process lifetime

    try:
        if sys.platform == "win32":
            import msvcrt

            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return handle
    except OSError:
        handle.close()
        return None


def configure_environment(data_dir: Path, resources: Path) -> None:
    """Set every env var `backend/app/config.py` reads, BEFORE
    `backend.app.main` (and therefore `backend.app.config`) is imported.
    """

    def posix(p: Path) -> str:
        return p.as_posix()

    os.environ.setdefault("DATABASE_URL", f"sqlite:///{posix(data_dir / 'app.db')}")
    os.environ.setdefault("USER_DATASETS_DIR", str(data_dir / "datasets" / "user"))
    os.environ.setdefault("MODELS_DIR", str(data_dir / "models"))
    os.environ.setdefault("BUILTIN_DATASET_CSV", str(resources / "datasets" / "builtin" / "results.csv"))
    os.environ.setdefault("INITIAL_MODEL_DIR", str(resources / "models" / "decision_tree" / "v1"))
    # Same-origin (pywebview loads http://127.0.0.1:PORT/, same as the API)
    # — CORS is irrelevant here, but the FastAPI app always applies its
    # CORSMiddleware, so this just needs to name our own origin.
    os.environ.setdefault("CORS_ALLOW_ORIGINS", "http://127.0.0.1")


LOG_MAX_BYTES = 2 * 1024 * 1024  # 2 MB
LOG_BACKUP_COUNT = 2  # app.log + app.log.1 + app.log.2, ~6 MB ceiling total

# Current log file path, tracked here (not just derived on demand) because
# it can change at runtime via apply_log_folder() (Settings page's "Change
# log folder" button) — register_system_routes reads this through
# current_log_path() rather than capturing a value that could go stale.
_current_log_path: Path | None = None


def log_folder_override_path() -> Path:
    """Pointer file recording a user-chosen custom log folder, if any.

    Deliberately lives next to the exe (not inside `data_dir`, and NOT in
    %APPDATA%) — it must be findable/stable regardless of where the user
    later points the actual log folder, and "a config file inside the
    user's own portable app folder" is expected, unlike scattering files
    on the system drive.
    """

    return exe_dir() / "log_folder.txt"


def read_log_folder_override() -> Path | None:
    pointer = log_folder_override_path()
    if not pointer.exists():
        return None
    try:
        text = pointer.read_text(encoding="utf-8").strip()
        return Path(text) if text else None
    except OSError:
        return None


def write_log_folder_override(folder: Path) -> None:
    log_folder_override_path().write_text(str(folder), encoding="utf-8")


def resolve_log_folder(data_dir: Path) -> Path:
    override = read_log_folder_override()
    if override is not None and _is_writable(override):
        return override
    return data_dir / "logs"


def current_log_path() -> Path:
    assert _current_log_path is not None, "setup_logging() must run first"
    return _current_log_path


def _build_rotating_handler(log_path: Path) -> logging.handlers.RotatingFileHandler:
    handler = logging.handlers.RotatingFileHandler(
        log_path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT, encoding="utf-8"
    )
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    return handler


def setup_logging(data_dir: Path) -> None:
    global _current_log_path

    log_folder = resolve_log_folder(data_dir)
    log_folder.mkdir(parents=True, exist_ok=True)
    log_path = log_folder / "app.log"
    _current_log_path = log_path

    # RotatingFileHandler: auto-cleanup, per the user's request — logs cap
    # out around LOG_MAX_BYTES * (LOG_BACKUP_COUNT + 1) instead of growing
    # forever. (There's also a manual "Clear log" action exposed via
    # /api/system/log for a user who wants to clear it immediately rather
    # than wait for rotation.)
    handlers: list[logging.Handler] = [_build_rotating_handler(log_path)]

    # PyInstaller's windowed (console=False) build runs under the GUI
    # subsystem with no attached console: sys.stdout/sys.stderr are None.
    # logging.StreamHandler() defaults to sys.stderr — adding it
    # unconditionally is harmless most of the time (Handler.handleError
    # swallows the resulting failure), but it's a needless extra thing
    # that can go wrong for zero benefit (nothing can see a console here
    # anyway), so it's only added when a real stream exists (dev mode, or
    # the `console=True` debug build).
    if sys.stderr is not None:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(level=logging.INFO, handlers=handlers, force=True)


def apply_log_folder(new_folder: Path) -> Path:
    """Switch logging to a new folder at runtime (no restart needed) and
    persist the choice for future launches. Raises OSError if the folder
    isn't writable — the caller (the /api/system/log/folder route) turns
    that into a 400 for the UI rather than letting it propagate.
    """

    global _current_log_path

    if not _is_writable(new_folder):
        raise OSError(f"{new_folder} is not writable")

    new_log_path = new_folder / "app.log"

    root_logger = logging.getLogger()
    for handler in list(root_logger.handlers):
        if isinstance(handler, logging.handlers.RotatingFileHandler):
            root_logger.removeHandler(handler)
            handler.close()

    root_logger.addHandler(_build_rotating_handler(new_log_path))
    _current_log_path = new_log_path

    write_log_folder_override(new_folder)
    logger.info("Log folder changed to %s by user via Settings.", new_folder)
    return new_log_path


def frontend_dist_dir(resources: Path) -> Path:
    """Locate the built Vue app under `resources`.

    In dev (not frozen), `resources` is the project root, and the build
    Vite actually produces lives at `frontend/dist/`. In the packaged app,
    `app.spec` copies that same `dist/` folder's CONTENTS to a flattened
    `frontend/` directory instead (see app.spec's `datas`), so it's found
    one level up from where it would be in dev. Trying the dev-shaped path
    first and falling back covers both without needing a `sys.frozen`
    check here too.
    """

    dev_shaped = resources / "frontend" / "dist"
    if dev_shaped.exists():
        return dev_shaped
    return resources / "frontend"


class SetLogFolderRequest(BaseModel):
    """Body schema for POST /api/system/log/folder.

    Must live at MODULE level, not nested inside register_system_routes()
    — this file has `from __future__ import annotations` (PEP 563), which
    makes every type annotation a lazily-evaluated string. FastAPI
    resolves those strings via the endpoint function's `__globals__`; a
    class defined inside another function is only reachable through that
    function's local scope, not `__globals__`, so FastAPI could not
    resolve it there and silently fell back to treating `folder` as a
    query parameter instead of the JSON body — reproduced and fixed while
    testing the "Change log folder" feature end-to-end (a POST with a
    JSON body got a 422 "field required" for a query param that was never
    supposed to exist).
    """

    folder: str


class DesktopJsApi:
    """Bridged to the frontend as `window.pywebview.api` (see pywebview's
    `js_api` mechanism) — the ONLY way to show a native "choose a folder"
    dialog, since a web page has no filesystem access to offer one itself.
    Only reachable from inside the pywebview window; the Web edition's
    Settings page feature-detects `window.pywebview` and hides anything
    that depends on this.
    """

    def choose_log_folder(self) -> str | None:
        import webview

        result = webview.windows[0].create_file_dialog(webview.FOLDER_DIALOG)
        return result[0] if result else None


def register_system_routes(fastapi_app, data_dir: Path) -> None:
    """Desktop-only `/api/system/*` routes: let the UI show/clear/relocate
    the log file instead of the user having to find it themselves.

    Deliberately NOT part of `backend/app/main.py` — the Web edition has
    no local log file to expose this way (its logs go to stdout / whatever
    the hosting platform captures), so these routes must not exist there.
    The frontend's Settings page treats a 404 on `/api/system/info` as
    "not running as the Desktop app" and hides this section accordingly.

    Must be registered BEFORE `mount_frontend`'s catch-all route (see that
    function's docstring for why route registration order matters here).
    """

    from fastapi import HTTPException, Response

    @fastapi_app.get("/api/system/info", tags=["system"])
    def system_info() -> dict:
        log_path = current_log_path()
        return {
            "is_desktop": True,
            "data_dir": str(data_dir),
            "log_path": str(log_path),
            "log_folder": str(log_path.parent),
            "log_size_bytes": log_path.stat().st_size if log_path.exists() else 0,
        }

    @fastapi_app.get("/api/system/log", tags=["system"])
    def get_log(lines: int = 500) -> Response:
        log_path = current_log_path()
        if not log_path.exists():
            return Response(content="(no log yet)", media_type="text/plain")
        # Read as bytes and decode leniently: a RotatingFileHandler can
        # truncate mid-rollover right at a read, and this is a diagnostic
        # view, not something that needs byte-perfect accuracy.
        text = log_path.read_bytes().decode("utf-8", errors="replace")
        tail = text.splitlines()[-lines:]
        return Response(content="\n".join(tail), media_type="text/plain")

    @fastapi_app.delete("/api/system/log", tags=["system"])
    def clear_log() -> dict:
        try:
            current_log_path().write_text("", encoding="utf-8")
        except OSError as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
        logger.info("Log cleared by user via Settings.")
        return {"cleared": True}

    @fastapi_app.post("/api/system/log/folder", tags=["system"])
    def set_log_folder(request: SetLogFolderRequest) -> dict:
        try:
            new_path = apply_log_folder(Path(request.folder))
        except OSError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        return {"log_path": str(new_path)}


def mount_frontend(fastapi_app, frontend_dist: Path) -> None:
    """Serve the built Vue frontend from the SAME FastAPI app that answers
    `/api/...` — desktop-only; the Web edition serves its frontend
    separately and must never gain this route.

    Registered AFTER `backend.app.main`'s own `app.include_router(...)`
    calls (which already ran at import time), so the explicit `/api/*`
    routes still match first — Starlette tries routes in registration
    order, and this catch-all is intentionally added last.
    """

    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    if not frontend_dist.exists():
        raise FileNotFoundError(
            f"Frontend build not found at {frontend_dist}. "
            "Run `npm run build` in frontend/ before packaging the desktop app."
        )

    fastapi_app.mount(
        "/assets", StaticFiles(directory=frontend_dist / "assets"), name="frontend-assets"
    )

    index_path = frontend_dist / "index.html"

    @fastapi_app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str):  # noqa: ARG001 - Vue Router (history mode) reads location itself
        return FileResponse(index_path)


def wait_for_server(port: int, timeout: float = 30.0) -> bool:
    import urllib.request

    deadline = time.monotonic() + timeout
    url = f"http://127.0.0.1:{port}/api/health"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as response:  # noqa: S310 - fixed localhost URL
                if response.status == 200:
                    return True
        except OSError:
            pass
        time.sleep(0.3)
    return False


def show_native_error(title: str, message: str) -> None:
    if sys.platform == "win32":
        import ctypes

        MB_ICONERROR = 0x10
        ctypes.windll.user32.MessageBoxW(None, message, title, MB_ICONERROR)
    else:
        print(f"{title}: {message}", file=sys.stderr)


def main() -> int:
    data_dir = app_data_dir()
    resources = resource_root()

    lock_handle = acquire_single_instance_lock(data_dir / ".instance-lock")
    if lock_handle is None:
        # Another instance is already running. There is no cross-process
        # IPC here to ask it to focus its window (see module docstring —
        # deliberately not rebuilding that machinery for a single-process
        # app); a short, unambiguous message is enough for what is, in
        # practice, a rare double-click.
        show_native_error(
            "FIFA Prediction",
            "FIFA Prediction is already running. Check your taskbar.",
        )
        return 0

    setup_logging(data_dir)
    logger.info("Starting up. resources=%s data_dir=%s frozen=%s", resources, data_dir, getattr(sys, "frozen", False))

    try:
        return _run(data_dir, resources)
    except Exception as error:  # noqa: BLE001 - last-resort catch-all, see docstring below
        # A windowed (console=False) build has no visible console and no
        # default place for an unhandled exception's traceback to go — it
        # would otherwise just look like the app silently hung or vanished
        # (reproduced during initial packaging: sys.stdout/sys.stderr are
        # None under the GUI subsystem, and some import along the way
        # apparently touches one of them). log.exception writes to the
        # FileHandler regardless (see setup_logging), and the MessageBox
        # guarantees the user sees SOMETHING instead of nothing.
        logger.exception("Unhandled error during startup.")
        show_native_error(
            "FIFA Prediction — Unexpected error",
            f"{error}\n\nDetails were written to: {current_log_path()}",
        )
        return 1
    finally:
        lock_handle.close()


def _run(data_dir: Path, resources: Path) -> int:
    configure_environment(data_dir, resources)

    # Imported only now: it must see the environment variables set above.
    import uvicorn
    from backend.app.main import app as fastapi_app

    register_system_routes(fastapi_app, data_dir)
    mount_frontend(fastapi_app, frontend_dist_dir(resources))

    port = 17872
    # log_config=None: uvicorn's default logging setup attaches a
    # StreamHandler to sys.stderr, which is None under PyInstaller's
    # windowed (console=False) build — the likely cause of an early,
    # silent hang found while first packaging this (no visible exception,
    # since there's no console to print one to; see main()'s catch-all for
    # the general version of this class of bug). backend/app/main.py
    # already calls logging.basicConfig() itself, so uvicorn's own log
    # config isn't needed anyway.
    config = uvicorn.Config(
        fastapi_app, host="127.0.0.1", port=port, log_level="warning", log_config=None
    )
    server = uvicorn.Server(config)

    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not wait_for_server(port):
        show_native_error(
            "FIFA Prediction — Backend failed to start",
            f"The local prediction service did not respond in time.\n\n"
            f"Details were written to: {current_log_path()}",
        )
        server.should_exit = True
        return 1

    logger.info("Backend ready on port %s. Opening window.", port)

    import webview

    # pywebview cancels every file download by default (WebView2's
    # DownloadStarting handler sets args.Cancel = True unless this is on) —
    # without it, the frontend's "Download Markdown"/"Download PDF" buttons
    # (blob-URL <a download> / jsPDF's doc.save(), see frontend/src/utils/
    # report.js) fail silently: no error, no dialog, nothing happens. With
    # it enabled, WebView2 shows its own native Save-As dialog per download.
    webview.settings["ALLOW_DOWNLOADS"] = True

    webview.create_window(
        "FIFA Prediction",
        f"http://127.0.0.1:{port}/",
        width=1320,
        height=880,
        min_size=(960, 640),
        js_api=DesktopJsApi(),
    )
    # storage_path: WebView2's own cookie/cache/local-storage profile.
    # pywebview defaults this to a folder under %APPDATA% — left
    # unconfigured, that would be a SECOND trace on the system drive
    # besides app_data_dir() above, defeating the "delete the folder,
    # nothing is left" requirement. Keeping it inside the same portable
    # data_dir consolidates the app's entire footprint into one place.
    webview.start(storage_path=str(data_dir / "webview2"))

    logger.info("Window closed. Shutting down backend.")
    server.should_exit = True
    server_thread.join(timeout=5)
    return 0


if __name__ == "__main__":
    sys.exit(main())
