# FIFA World Cup Match Prediction

Predicts international football match outcomes (Home Win / Draw / Home
Loss) from historical team form, goal statistics, tournament context, and
pre-match Elo team ratings. Originally a Data Mining coursework Colab
notebook; this repository is the production version, shipped as both a **Web
application** and a **Windows Desktop application**, sharing one
machine-learning core so both editions produce identical predictions for
the same input.

```
                    core/  (shared ML: features, training, prediction)
                       │
          ┌────────────┴────────────┐
       Web Edition              Desktop Edition
     Vue 3 + FastAPI         Vue 3 + FastAPI + pywebview
          │                    (one process, WebView2 window)
        MySQL                          │
                                     SQLite
```

## Repository layout

| Folder | Purpose |
|---|---|
| [`core/`](core) | Shared ML logic — preprocessing, feature engineering, models, prediction. No web framework or database code lives here. |
| [`database/`](database) | Repository layer shared by both editions (SQLAlchemy models + repositories); one code path works against both MySQL and SQLite. |
| [`backend/`](backend) | FastAPI service layer (API routes, business services) used by both editions. |
| [`frontend/`](frontend) | Vue 3 + Vite UI — one `npm run build` output consumed by both editions. |
| [`desktop_app/`](desktop_app) | pywebview + PyInstaller packaging that turns `backend/` + `frontend/` into a single-process Windows executable. |
| [`datasets/`](datasets) | `builtin/` — the protected, read-only default dataset. `user/` — uploaded dataset versions (gitignored). |
| [`models/`](models) | Trained model artifacts (`model.joblib` + `metadata.json` per version). |
| [`tests/`](tests) | Tests for `core/` and `database/`, including parity checks against the original notebook. |
| [`scripts/`](scripts) | One-off tooling: train/export a model, validate `core/` against the notebook, bootstrap a dev database. |

## Web Version

### Prerequisites

- Python 3.11+ and Node.js 18+
- A MySQL 8+ server for production (local development defaults to SQLite —
  no MySQL needed until you're ready to deploy)

### Backend setup

```bash
python -m venv .venv
.venv/Scripts/pip install -r backend/requirements.txt
```

Runs against SQLite with zero configuration (see
[`backend/README.md`](backend/README.md) for the full environment variable
reference). To use MySQL instead:

```bash
export DATABASE_URL="mysql+pymysql://<user>:<password>@<host>:3306/<database>"
```

Create the target database first (`CREATE DATABASE fifa_prediction;`) —
tables are created automatically on first startup
(`database.bootstrap.bootstrap_database`); there is no separate migration
step to run for a fresh database. The built-in dataset and both built-in
models are also registered automatically on first startup — no manual
dataset/model initialization needed.

```bash
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

Docs at http://localhost:8000/docs. Never commit real database credentials
— set `DATABASE_URL` via your deployment platform's environment variable
mechanism, not a checked-in file.

### Frontend setup

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 — the dev server proxies `/api/*` to the
backend on port 8000. See [`frontend/README.md`](frontend/README.md) for
the production build and `VITE_API_BASE_URL` if the backend is deployed on
a different origin.

## Desktop Version (Windows)

### Requirements

Windows 10 (1803+) or 11, 64-bit. **No Python, Node.js, or MySQL
installation required** — everything needed is bundled into the release,
except the WebView2 Runtime, which is already present on nearly every
Windows 10/11 machine (built into Windows 11; auto-installed via Windows
Update on Windows 10).

### Installing

1. Go to this repository's [Releases](../../releases) page.
2. Download `FIFA-Prediction-win-x64.zip`.
3. Extract it into any folder — it contains just `FIFA-Prediction.exe`,
   `FIFA-Prediction.exe.config`, an `_internal\` folder, and `LICENSE` —
   and run `FIFA-Prediction.exe`. Keep the `.config` file next to the exe.
   No installer, no admin rights, no install-location wizard.
4. Predictions work immediately and fully offline.

The window appears within a couple of seconds with a loading screen while
the prediction engine starts. The very first launch of a freshly
downloaded executable can take longer — Windows Defender/SmartScreen scans
a new, unsigned binary once. See
[`desktop_app/README.md`](desktop_app/README.md#troubleshooting) if it
seems stuck.

### Application data location

Fully portable: everything the app writes stays in a `data\` folder next
to `FIFA-Prediction.exe`. Deleting the extracted folder removes the app
completely — nothing is left in `%APPDATA%` or anywhere else.

```
<extracted folder>\
├── FIFA-Prediction.exe
├── FIFA-Prediction.exe.config   # required — lets .NET load the bundled DLLs
├── _internal\           # bundled runtime, built-in dataset and production model (read-only)
├── LICENSE
└── data\                # created on first launch
    ├── app.db           # SQLite database (datasets/models/predictions metadata)
    ├── datasets\user\   # your uploaded dataset versions
    ├── models\          # models you've trained
    ├── webview2\        # the window's browser cache
    └── logs\app.log     # startup + runtime log (folder changeable in Settings)
```

To update, extract the new release and copy your old `data\` folder next
to the new `FIFA-Prediction.exe`.

### Uploading a dataset / retraining a model

Same workflow as the Web edition's Dataset Management / Model Management
pages — Dataset Management → Upload → Activate; Model Management → Train
a new model → Activate. See [`backend/README.md`](backend/README.md)'s API
table for what each action does.

### Troubleshooting

See [`desktop_app/README.md`](desktop_app/README.md#troubleshooting).

## Development

### Architecture

```
Browser (Web)  /  pywebview window (Desktop)
        │
     Vue 3 (frontend/)
        │  HTTP (axios)
     FastAPI (backend/)
        │
  Service layer (backend/app/services/)
        │
Repository layer (database/) ──┬── MySQL   (Web)
                                └── SQLite  (Desktop)
        │
   core/ (shared ML: same feature engineering + model for both editions)
```

The Desktop edition runs the Vue build, FastAPI, and the ML core in ONE
Python process (see [`desktop_app/main.py`](desktop_app/main.py)) — there
is no separate desktop shell process or IPC layer to keep in sync with the
Web edition; only the database engine and a few filesystem paths differ.

Reproducibility: every prediction response and history record carries the
exact `dataset_version` and `model_version` used to produce it — a
prediction always uses the dataset its active model was actually trained
on, never whatever dataset happens to be separately flagged "active" (see
`backend/app/services/feature_service.py`'s module docstring for why).

### Testing

```bash
.venv/Scripts/python.exe -m pytest tests backend/tests -v   # core + database + API
.venv/Scripts/python.exe scripts/validate_against_notebook.py  # core/ vs. the original notebook, bit-for-bit
```

### Build process

- **Web**: `frontend/` (`npm run build`) + `backend/` deployed as a normal
  Python/Node service pair — see each folder's README.
- **Desktop**: see [`desktop_app/README.md`](desktop_app/README.md) —
  `desktop_app/build_release.py` builds the frontend, bundles everything
  with PyInstaller, and writes the release zip to `desktop_app/release/`.

## Models

| Built-in model | Features | Accuracy* | World Cup* |
|---|---|---|---|
| `logistic_regression_elo_v1` (default) | `feature_v2`: team form + Elo ratings | 59.4% | 56.6% |
| `decision_tree_v1` (original notebook) | `feature_v1`: the notebook's 23 features | 51.2% | 46.1% |

\* Rolling-window validation: for each two-year window from 2010 to 2025,
trained only on earlier matches (15,506 test matches, 256 World Cup
matches). Always predicting "Home Win" scores 47.6%.

`feature_v2` adds pre-match Elo ratings computed from the same dataset
with the published World Football Elo rules
([`core/feature_engineering/elo.py`](core/feature_engineering/elo.py)).
`feature_v1` and the original Decision Tree are unchanged and still pass
the bit-for-bit notebook parity tests. Both feature sets, and every model
type (including a soft-voting ensemble), can be trained from Model
Management.

## Upset risk

The **Upset Risk** page, every prediction, the history list, and the
Markdown/PDF reports show the probability that the underdog — the side the
active model gives the lower win chance — wins outright (draws excluded):
low below 15%, medium 15–30%, high above 30%, with a prominent
"HIGH-RISK PREDICTION" mark above 30%. With the Elo model this probability
is well calibrated (held-out matches it rated 30–40% ended in an upset
33.5% of the time).

The page also lists each team's historical upsets with dates: completed
matches the underdog won although the model gave it under 20% beforehand
([`core/analytics/upset.py`](core/analytics/upset.py)).

## Known limitations

No player-level data, injuries, or suspensions; no FIFA ranking; a fixed
5-match recent-form window; draws remain the hardest class to predict.
Predictions are statistical estimates for reference only — see the in-app
disclaimer.

## License

Copyright (c) 2026 LIZHE. All rights reserved — the source is viewable for
reference only; see [`LICENSE`](LICENSE).
