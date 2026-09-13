# FIFA Prediction — Frontend (Vue 3 + Vite)

Talks to the FastAPI backend in `../backend/`. See that folder's README for
how to run the backend.

## Setup

```bash
cd frontend
npm install
```

## Run (development)

Start the backend first (`uvicorn backend.app.main:app --reload --port 8000`
from the project root), then in a second terminal:

```bash
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api/*` requests to
`http://localhost:8000` (configured in `vite.config.js`) — no `.env` needed
for local development.

## Build (production)

```bash
npm run build
```

Outputs static files to `dist/`. If the backend is not served from the same
origin, copy `.env.example` to `.env.production` and set
`VITE_API_BASE_URL` to the backend's URL before building.

## Structure

```
src/
├── components/       # TeamSelector, PredictionForm, PredictionResult,
│                      ProbabilityChart, DatasetManager, ModelManager
├── views/            # HomeView, PredictionView, DatasetView, ModelView,
│                      HistoryView — one per route
├── stores/           # Pinia: predictionStore, datasetStore, modelStore
├── services/api.js   # Single axios client — the only place that knows
│                      about backend endpoint paths/payload shapes
└── router/index.js
```

## Pages

| Route | Page | Purpose |
|---|---|---|
| `/` | Home | Overview: active dataset, active model, quick prediction |
| `/predict` | Prediction | Full match prediction form + probability chart |
| `/datasets` | Dataset Management | Upload, validate, activate, delete dataset versions |
| `/models` | Model Management | Train new models, view metrics, activate a model version |
| `/history` | Prediction History | All past predictions |
