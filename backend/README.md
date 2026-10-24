# FIFA Prediction — Backend (FastAPI)

Shared service layer on top of `core/` (ML) and `database/` (repositories).
Serves both the Web frontend and the Desktop app — the Desktop app
(`desktop_app/main.py`) imports this exact FastAPI `app` object and runs
it in a background thread inside the same process as its pywebview
window, rather than as a separate bundled executable.

## Setup

```bash
python -m venv .venv          # from the project root, if not already created
.venv/Scripts/pip install -r backend/requirements.txt
```

## Run (development, SQLite)

No configuration needed — defaults to a local SQLite file at
`backend/dev-data/app.db`, auto-created and auto-bootstrapped (built-in
dataset + both built-in models registered, the Elo logistic regression
active) on first startup.

```bash
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --reload --port 8000
```

Then open:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc
- http://localhost:8000/api/health

## Run against MySQL (production / Web)

Set `DATABASE_URL` before starting the process — nothing else changes,
since `database/` contains no MySQL/SQLite-specific SQL:

```bash
export DATABASE_URL="mysql+pymysql://<user>:<password>@<host>:3306/<database>"
.venv/Scripts/python.exe -m uvicorn backend.app.main:app --port 8000
```

Create the target MySQL database first (`CREATE DATABASE fifa_prediction;`)
— table creation itself happens automatically via `bootstrap_database` on
startup. Never commit real credentials; use `.env` + `.env.example`
(added when the frontend needs it too) and export environment variables
via your process manager/deployment platform in production.

## Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///backend/dev-data/app.db` | SQLAlchemy connection URL |
| `BUILTIN_DATASET_CSV` | `datasets/builtin/results.csv` | Protected built-in dataset |
| `USER_DATASETS_DIR` | `datasets/user/` | Where uploaded CSVs are stored |
| `MODELS_DIR` | `models/` | Where newly trained model artifacts are stored |
| `BUILTIN_MODELS_DIR` | `models/` | Root of the shipped built-in models (`decision_tree/v1`, `logistic_regression/elo_v1` — the latter active on a fresh database) |
| `CORS_ALLOW_ORIGINS` | `http://localhost:5173` | Comma-separated allowed origins (Vite dev server) |
| `MAX_UPLOAD_SIZE_BYTES` | `52428800` (50 MB) | Dataset upload size limit |

## API surface

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Liveness check |
| GET | `/api/teams` | Known team names (for dropdowns) |
| POST | `/api/predictions` | Predict a hypothetical match (response includes `upset_probability` / `upset_risk_level`) |
| POST | `/api/upsets/risk` | Upset risk for a hypothetical match — same body as `/api/predictions`, not recorded in history |
| GET | `/api/upsets/teams/{team}` | A team's historical upsets (underdog won with < 20% pre-match chance), most recent first, plus caused/suffered counts |
| GET | `/api/history` | Recent prediction history |
| GET | `/api/datasets` | List dataset versions |
| POST | `/api/datasets/upload` | Upload a new dataset version (multipart `file`) |
| POST | `/api/datasets/{id}/activate` | Mark a dataset as current (does not affect live predictions by itself) |
| DELETE | `/api/datasets/{id}` | Delete an uploaded dataset (built-in is protected: 403) |
| GET | `/api/models` | List trained model versions |
| POST | `/api/models/train` | Train a new model on a given dataset (defaults: `model_type="logistic_regression"`, `feature_version="feature_v2"`) |
| POST | `/api/models/{id}/activate` | Activate a model version — this IS what changes live predictions |

**Important**: predictions always use the **active model's own training
dataset**, not whatever dataset is separately flagged "active" — this
keeps predictions reproducible even if a different dataset is uploaded and
activated later without retraining. See
`backend/app/services/feature_service.py` for the full rationale.

## Tests

```bash
.venv/Scripts/python.exe -m pytest backend/tests -v
```

Runs against a throwaway temp SQLite DB (never touches `dev-data/`), and
cross-checks one prediction against `core/` called directly to guard
against the HTTP/service layer silently distorting a result.
