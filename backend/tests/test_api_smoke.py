"""Stage 3 end-to-end smoke test: the full FastAPI app, exercised through
its actual HTTP interface (FastAPI's TestClient), against a throwaway
SQLite DB and a throwaway user-datasets directory — never touching the
real dev-data/ or datasets/user/ used by manual `uvicorn` runs.

Environment variables must be set BEFORE `backend.app.config` is imported
anywhere (including transitively via `backend.app.main`), since
`Settings` reads them at class-body evaluation time. This file is only
safe to run as its own pytest session/process — see the module-level
os.environ block below.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_TEST_DATA_DIR = Path(tempfile.mkdtemp(prefix="fifa_backend_test_"))

os.environ["DATABASE_URL"] = f"sqlite:///{(_TEST_DATA_DIR / 'test.db').as_posix()}"
os.environ["USER_DATASETS_DIR"] = str(_TEST_DATA_DIR / "datasets_user")
os.environ["MODELS_DIR"] = str(_TEST_DATA_DIR / "models")
os.environ["BUILTIN_DATASET_CSV"] = str(
    PROJECT_ROOT / "datasets" / "builtin" / "results.csv"
)
os.environ["BUILTIN_MODELS_DIR"] = str(PROJECT_ROOT / "models")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.app.main import app  # noqa: E402


@pytest.fixture(scope="module", autouse=True)
def cleanup_test_data():
    yield
    shutil.rmtree(_TEST_DATA_DIR, ignore_errors=True)


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_builtin_dataset_and_model_are_bootstrapped_active(client):
    datasets = client.get("/api/datasets").json()
    assert len(datasets) == 1
    builtin = datasets[0]
    assert builtin["is_builtin"] is True
    assert builtin["is_active"] is True
    assert builtin["row_count"] == 49520

    models = {m["model_id"]: m for m in client.get("/api/models").json()}
    assert set(models) == {"decision_tree_v1", "logistic_regression_elo_v1"}
    assert all(m["is_builtin"] for m in models.values())
    assert models["logistic_regression_elo_v1"]["is_active"] is True
    assert models["logistic_regression_elo_v1"]["feature_version"] == "feature_v2"
    assert models["decision_tree_v1"]["feature_version"] == "feature_v1"


def test_teams_endpoint_lists_known_teams(client):
    response = client.get("/api/teams")
    assert response.status_code == 200
    teams = response.json()
    assert "England" in teams
    assert "Argentina" in teams
    assert teams == sorted(teams)


@pytest.mark.parametrize(
    "model_id, artifact_subdir",
    [
        ("logistic_regression_elo_v1", ("logistic_regression", "elo_v1")),
        ("decision_tree_v1", ("decision_tree", "v1")),
    ],
)
def test_prediction_endpoint_matches_core_directly(client, model_id, artifact_subdir):
    models = client.get("/api/models").json()
    default_id = next(m["id"] for m in models if m["is_active"])
    target_id = next(m["id"] for m in models if m["model_id"] == model_id)
    client.post(f"/api/models/{target_id}/activate")

    response = client.post(
        "/api/predictions",
        json={
            "home_team": "England",
            "away_team": "Argentina",
            "host_country": "United States",
            "tournament": "FIFA World Cup",
        },
    )
    client.post(f"/api/models/{default_id}/activate")
    assert response.status_code == 200
    body = response.json()

    assert body["predicted_outcome"] in {"Home Win", "Draw", "Home Loss"}
    assert body["model_version"] == model_id
    assert body["dataset_version"] == "builtin_v1"
    assert abs(sum(body["probabilities"].values()) - 1.0) < 1e-9

    # Cross-check against core/ directly, bypassing the API/service layer,
    # to confirm the HTTP layer doesn't distort the prediction (Development
    # Prompt.md Section 29: Colab == Web == Desktop for the same input).
    from core.dataset.io import load_raw_dataset
    from core.models.registry import load_model_artifact
    from core.pipeline import run_feature_pipeline
    from core.prediction.predictor import predict_match
    from core.prediction.team_state import build_team_latest_state_index

    loaded = load_model_artifact(PROJECT_ROOT / "models" / Path(*artifact_subdir))
    df_raw = load_raw_dataset(PROJECT_ROOT / "datasets" / "builtin" / "results.csv")
    pipeline_result = run_feature_pipeline(df_raw, loaded.metadata.feature_version)
    team_state_index = build_team_latest_state_index(
        pipeline_result.featured_data, pipeline_result.elo_ratings
    )
    assert pipeline_result.feature_columns == loaded.metadata.feature_columns

    direct_result = predict_match(
        home_team="England",
        away_team="Argentina",
        host_country="United States",
        tournament="FIFA World Cup",
        model=loaded.model,
        scaler=loaded.scaler,
        team_state_index=team_state_index,
        cold_start_fill_values=pipeline_result.cold_start_fill_values,
        tournament_dummy_columns=pipeline_result.tournament_dummy_columns,
        feature_columns=pipeline_result.feature_columns,
    )

    assert body["predicted_outcome"] == direct_result.predicted_outcome
    for outcome_class, probability in direct_result.probabilities.items():
        assert abs(body["probabilities"][outcome_class] - probability) < 1e-9


def test_prediction_is_recorded_in_history(client):
    history_before = client.get("/api/history").json()

    client.post(
        "/api/predictions",
        json={
            "home_team": "Brazil",
            "away_team": "Germany",
            "host_country": "Brazil",
            "tournament": "Friendly",
        },
    )

    history_after = client.get("/api/history").json()
    assert len(history_after) == len(history_before) + 1
    assert history_after[0]["home_team"] == "Brazil"
    assert history_after[0]["away_team"] == "Germany"


def test_builtin_dataset_cannot_be_deleted_via_api(client):
    datasets = client.get("/api/datasets").json()
    builtin_id = next(d["id"] for d in datasets if d["is_builtin"])

    response = client.delete(f"/api/datasets/{builtin_id}")
    assert response.status_code == 403


def test_upload_train_and_switch_to_new_dataset(client):
    # A small but valid CSV (subset of the real schema) uploaded as a new
    # user dataset version.
    csv_content = (
        "date,home_team,away_team,home_score,away_score,tournament,city,country,neutral\n"
        "2020-01-01,TestTeamA,TestTeamB,2,1,Friendly,TestCity,TestCountry,FALSE\n"
        "2020-01-08,TestTeamB,TestTeamA,0,0,Friendly,TestCity2,TestCountry,FALSE\n"
        "2020-01-15,TestTeamA,TestTeamB,3,3,Friendly,TestCity,TestCountry,FALSE\n"
    )

    upload_response = client.post(
        "/api/datasets/upload",
        files={"file": ("my_upload.csv", csv_content.encode("utf-8"), "text/csv")},
    )
    assert upload_response.status_code == 200
    upload_body = upload_response.json()
    assert upload_body["dataset"]["version_label"] == "user_v1"
    assert upload_body["dataset"]["validation_status"] == "valid"
    assert upload_body["dataset"]["is_active"] is False

    new_dataset_id = upload_body["dataset"]["id"]

    activate_response = client.post(f"/api/datasets/{new_dataset_id}/activate")
    assert activate_response.status_code == 200
    assert activate_response.json()["is_active"] is True

    # The previously-active builtin dataset must now be inactive.
    datasets = client.get("/api/datasets").json()
    builtin = next(d for d in datasets if d["is_builtin"])
    assert builtin["is_active"] is False

    # Activating a dataset does NOT by itself change what predictions use —
    # predictions always follow the ACTIVE MODEL's own training dataset
    # (see feature_service module docstring). The active model is still
    # the built-in default, trained on builtin_v1, so predictions must keep
    # reporting builtin_v1 until a new model is trained and activated.
    predict_response = client.post(
        "/api/predictions",
        json={
            "home_team": "England",
            "away_team": "Argentina",
            "host_country": "United States",
            "tournament": "FIFA World Cup",
        },
    )
    assert predict_response.status_code == 200
    assert predict_response.json()["dataset_version"] == "builtin_v1"
    assert predict_response.json()["model_version"] == "logistic_regression_elo_v1"

    # Train a brand new model on the uploaded dataset and switch to it.
    train_response = client.post(
        "/api/models/train", json={"dataset_id": new_dataset_id, "model_type": "decision_tree"}
    )
    assert train_response.status_code == 200
    new_model = train_response.json()
    assert new_model["model_id"] == "decision_tree_v2"
    assert new_model["dataset_id"] == new_dataset_id
    assert new_model["is_active"] is False

    activate_model_response = client.post(f"/api/models/{new_model['id']}/activate")
    assert activate_model_response.status_code == 200
    assert activate_model_response.json()["is_active"] is True

    predict_response_2 = client.post(
        "/api/predictions",
        json={
            "home_team": "TestTeamA",
            "away_team": "TestTeamB",
            "host_country": "TestCountry",
            "tournament": "Friendly",
        },
    )
    assert predict_response_2.status_code == 200
    assert predict_response_2.json()["model_version"] == "decision_tree_v2"
    assert predict_response_2.json()["dataset_version"] == "user_v1"

    # Restore the builtin dataset as active so it doesn't leak into other
    # tests if pytest ever reorders/parallelises within this module.
    builtin_id = builtin["id"]
    restore_response = client.post(f"/api/datasets/{builtin_id}/activate")
    assert restore_response.status_code == 200


# --- Team Explorer (team-stats) -----------------------------------------


def test_team_stats_list_teams_reflects_active_dataset(client):
    response = client.get("/api/team-stats/teams")
    assert response.status_code == 200
    teams = response.json()
    assert "England" in teams
    assert "Argentina" in teams


def test_team_stats_matches_most_recent_first(client):
    response = client.get("/api/team-stats/England/matches", params={"limit": 5})
    assert response.status_code == 200
    matches = response.json()
    assert len(matches) == 5
    dates = [m["date"] for m in matches]
    assert dates == sorted(dates, reverse=True)
    assert all(m["outcome"] in {"Win", "Draw", "Loss"} for m in matches)


def test_team_stats_for_known_team(client):
    response = client.get("/api/team-stats/England/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["team_name"] == "England"
    assert stats["matches_played"] > 0
    assert stats["wins"] + stats["draws"] + stats["losses"] == stats["matches_played"]
    assert 0 <= stats["rating"] <= 100


def test_team_stats_for_unknown_team_returns_404(client):
    response = client.get("/api/team-stats/Definitely Not A Team FC/stats")
    assert response.status_code == 404


def test_team_stats_compare_sorted_by_rating(client):
    response = client.post(
        "/api/team-stats/compare",
        json={"team_names": ["England", "Argentina", "Brazil"]},
    )
    assert response.status_code == 200
    results = response.json()
    assert {r["team_name"] for r in results} == {"England", "Argentina", "Brazil"}
    ratings = [r["rating"] for r in results]
    assert ratings == sorted(ratings, reverse=True)


def test_team_stats_compare_rejects_more_than_five_teams(client):
    response = client.post(
        "/api/team-stats/compare",
        json={"team_names": ["England", "Argentina", "Brazil", "France", "Spain", "Germany"]},
    )
    assert response.status_code == 422  # Pydantic max_length on the request body


# --- Model deletion -------------------------------------------------------


def test_builtin_model_cannot_be_deleted_via_api(client):
    models = client.get("/api/models").json()
    builtin_model_id = next(m["id"] for m in models if m["model_id"] == "decision_tree_v1")

    response = client.delete(f"/api/models/{builtin_model_id}")
    assert response.status_code == 403


def test_active_model_cannot_be_deleted_via_api(client):
    models = client.get("/api/models").json()
    active_model_id = next(m["id"] for m in models if m["is_active"])

    response = client.delete(f"/api/models/{active_model_id}")
    assert response.status_code == 400


def test_non_builtin_inactive_model_can_be_deleted_via_api(client):
    datasets = client.get("/api/datasets").json()
    builtin_dataset_id = next(d["id"] for d in datasets if d["is_builtin"])

    train_response = client.post(
        "/api/models/train",
        json={"dataset_id": builtin_dataset_id, "model_type": "logistic_regression"},
    )
    assert train_response.status_code == 200
    scratch_model = train_response.json()
    assert scratch_model["is_active"] is False

    delete_response = client.delete(f"/api/models/{scratch_model['id']}")
    assert delete_response.status_code == 204

    models_after = client.get("/api/models").json()
    assert all(m["id"] != scratch_model["id"] for m in models_after)


# --- Prediction history: stats, delete, clear ----------------------------


def test_history_stats_reflects_recorded_predictions(client):
    before = client.get("/api/history/stats").json()

    client.post(
        "/api/predictions",
        json={
            "home_team": "Japan",
            "away_team": "South Korea",
            "host_country": "Japan",
            "tournament": "Friendly",
        },
    )

    after = client.get("/api/history/stats").json()
    assert after["total"] == before["total"] + 1
    assert sum(after["by_outcome"].values()) == after["total"]
    assert sum(bucket["count"] for bucket in after["confidence_buckets"]) == after["total"]


def test_delete_single_history_record(client):
    history_before = client.get("/api/history").json()
    target_id = history_before[0]["id"]

    delete_response = client.delete(f"/api/history/{target_id}")
    assert delete_response.status_code == 204

    history_after = client.get("/api/history").json()
    assert all(item["id"] != target_id for item in history_after)


def test_clear_all_history(client):
    # Make sure there is at least one record to clear.
    client.post(
        "/api/predictions",
        json={
            "home_team": "Mexico",
            "away_team": "Canada",
            "host_country": "Mexico",
            "tournament": "Friendly",
        },
    )

    clear_response = client.delete("/api/history")
    assert clear_response.status_code == 200
    assert clear_response.json()["deleted_count"] > 0

    history_after = client.get("/api/history").json()
    assert history_after == []

    stats_after = client.get("/api/history/stats").json()
    assert stats_after["total"] == 0


# --- Upset risk -------------------------------------------------------------


def _activate_default_builtin(client):
    models = client.get("/api/models").json()
    default_id = next(m["id"] for m in models if m["model_id"] == "logistic_regression_elo_v1")
    client.post(f"/api/models/{default_id}/activate")


MATCH = {
    "home_team": "Brazil",
    "away_team": "Germany",
    "host_country": "Brazil",
    "tournament": "FIFA World Cup",
}


def test_predictions_and_history_carry_upset_risk(client):
    _activate_default_builtin(client)

    body = client.post("/api/predictions", json=MATCH).json()
    probabilities = body["probabilities"]
    expected = min(probabilities["Home Win"], probabilities["Home Loss"])
    assert abs(body["upset_probability"] - expected) < 1e-12
    assert body["upset_risk_level"] in {"low", "medium", "high"}
    assert body["upset_favorite_outcome"] in {"Home Win", "Home Loss"}

    latest = client.get("/api/history").json()[0]
    assert latest["id"] == body["prediction_id"]
    assert latest["upset_probability"] == body["upset_probability"]
    assert latest["upset_risk_level"] == body["upset_risk_level"]


def test_upset_risk_endpoint_matches_prediction_and_is_not_recorded(client):
    _activate_default_builtin(client)
    prediction = client.post("/api/predictions", json=MATCH).json()
    history_count = len(client.get("/api/history", params={"limit": 500}).json())

    response = client.post("/api/upsets/risk", json=MATCH)
    assert response.status_code == 200
    risk = response.json()
    assert risk["upset_probability"] == prediction["upset_probability"]
    assert risk["model_version"] == "logistic_regression_elo_v1"
    assert len(client.get("/api/history", params={"limit": 500}).json()) == history_count


def test_team_upsets_lists_dated_upsets_below_threshold(client):
    _activate_default_builtin(client)

    response = client.get("/api/upsets/teams/Brazil", params={"limit": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["team"] == "Brazil"
    assert body["max_probability"] == 0.2
    assert body["summary"]["matches"] > 1000
    assert body["summary"]["upsets_caused"] + body["summary"]["upsets_suffered"] >= len(body["matches"])

    matches = body["matches"]
    assert 0 < len(matches) <= 10
    assert [m["date"] for m in matches] == sorted((m["date"] for m in matches), reverse=True)
    for m in matches:
        assert m["upset_probability"] < 0.2
        assert "Brazil" in (m["home_team"], m["away_team"])
        assert (m["role"] == "caused") == (m["winner"] == "Brazil")


def test_team_upsets_for_unknown_team_is_empty(client):
    _activate_default_builtin(client)

    body = client.get("/api/upsets/teams/Atlantis FC").json()
    assert body["summary"] == {"matches": 0, "upsets_caused": 0, "upsets_suffered": 0}
    assert body["matches"] == []
