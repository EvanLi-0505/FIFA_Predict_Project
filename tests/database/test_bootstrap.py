"""Bootstrap behaviour: built-in model registration/activation rules, plus
a regression test for a real bug found during Stage 5 desktop QA: the
built-in dataset's `file_path` (and the built-in models' `artifact_path`)
were only ever written on the very first bootstrap call. If that first
value was ever wrong for any reason — or the app is later reinstalled to a
different location — every dataset-dependent endpoint breaks permanently
for that user, with no way to recover short of deleting their database by
hand. `bootstrap_database` must re-sync both paths to whatever the CURRENT
process actually points at on every startup, not just the first one.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from sqlalchemy.exc import IntegrityError

from core.models.registry import ModelMetadata, save_model_artifact
from core.models.definitions import make_decision_tree
from database.bootstrap import bootstrap_database
from database.engine import create_all_tables, create_db_engine, create_session_factory
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
)

CSV_HEADER = "date,home_team,away_team,home_score,away_score,tournament,city,country,neutral\n"
CSV_ROWS = (
    "2020-01-01,TeamA,TeamB,2,1,Friendly,CityA,CountryA,FALSE\n"
    "2020-01-08,TeamB,TeamA,0,0,Friendly,CityB,CountryA,FALSE\n"
)


@pytest.fixture
def session():
    engine = create_db_engine("sqlite:///:memory:")
    create_all_tables(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        yield session, engine


def _write_csv(path: Path) -> Path:
    path.write_text(CSV_HEADER + CSV_ROWS, encoding="utf-8")
    return path


def test_builtin_dataset_path_resyncs_on_every_startup(session, tmp_path):
    session, engine = session
    dataset_repo = DatasetRepositoryImpl()

    original_dir = tmp_path / "original"
    original_dir.mkdir()
    original_csv = _write_csv(original_dir / "results.csv")

    bootstrap_database(engine, session, builtin_dataset_csv=original_csv)
    builtin = dataset_repo.get_by_version_label(session, "builtin_v1")
    assert builtin.file_path == str(original_csv)
    assert builtin.row_count == 2

    # Simulate a reinstall / drive change / the exact staleness bug found in
    # QA: the CSV now lives somewhere else entirely (with different data).
    moved_dir = tmp_path / "reinstalled"
    moved_dir.mkdir()
    moved_csv = moved_dir / "results.csv"
    moved_csv.write_text(
        CSV_HEADER + CSV_ROWS + "2020-01-15,TeamA,TeamB,3,3,Friendly,CityA,CountryA,FALSE\n",
        encoding="utf-8",
    )

    bootstrap_database(engine, session, builtin_dataset_csv=moved_csv)

    refreshed = dataset_repo.get_by_version_label(session, "builtin_v1")
    assert refreshed.id == builtin.id  # same row — never re-created
    assert refreshed.file_path == str(moved_csv)
    assert refreshed.row_count == 3
    assert refreshed.validation_status == "valid"


def test_builtin_model_artifact_path_resyncs_on_every_startup(session, tmp_path):
    session, engine = session
    model_repo = ModelVersionRepositoryImpl()

    csv_path = _write_csv(tmp_path / "results.csv")

    original_model_dir = tmp_path / "models_v1" / "decision_tree" / "v1"
    _save_dummy_model(original_model_dir)

    bootstrap_database(
        engine,
        session,
        builtin_dataset_csv=csv_path,
        builtin_model_dirs=[original_model_dir],
    )
    model = model_repo.get_by_model_id(session, "decision_tree_v1")
    assert model.artifact_path == str(original_model_dir)

    moved_model_dir = tmp_path / "models_v2" / "decision_tree" / "v1"
    _save_dummy_model(moved_model_dir)

    bootstrap_database(
        engine,
        session,
        builtin_dataset_csv=csv_path,
        builtin_model_dirs=[moved_model_dir],
    )

    refreshed = model_repo.get_by_model_id(session, "decision_tree_v1")
    assert refreshed.id == model.id  # same row — never re-created
    assert refreshed.artifact_path == str(moved_model_dir)


def _two_builtin_models(tmp_path: Path) -> tuple[Path, Path]:
    original = tmp_path / "models" / "decision_tree" / "v1"
    elo = tmp_path / "models" / "logistic_regression" / "elo_v1"
    _save_dummy_model(original)
    _save_dummy_model(elo, model_id="logistic_regression_elo_v1")
    return original, elo


def _active_model_id(session) -> str:
    return ModelVersionRepositoryImpl().get_active(session).model_id


def test_fresh_install_registers_all_builtins_and_activates_default(session, tmp_path):
    session, engine = session
    csv_path = _write_csv(tmp_path / "results.csv")
    original, elo = _two_builtin_models(tmp_path)

    bootstrap_database(
        engine, session, builtin_dataset_csv=csv_path,
        builtin_model_dirs=[original, elo], default_model_dir=elo,
    )

    models = ModelVersionRepositoryImpl().list_all(session)
    assert {m.model_id for m in models} == {"decision_tree_v1", "logistic_regression_elo_v1"}
    assert all(m.is_builtin for m in models)
    assert _active_model_id(session) == "logistic_regression_elo_v1"


def test_upgrade_switches_from_old_builtin_to_new_default_once(session, tmp_path):
    session, engine = session
    csv_path = _write_csv(tmp_path / "results.csv")
    original, elo = _two_builtin_models(tmp_path)

    # A v2.0 database: only the original built-in model, active.
    bootstrap_database(engine, session, builtin_dataset_csv=csv_path, builtin_model_dirs=[original])
    assert _active_model_id(session) == "decision_tree_v1"

    bootstrap_database(
        engine, session, builtin_dataset_csv=csv_path,
        builtin_model_dirs=[original, elo], default_model_dir=elo,
    )
    assert _active_model_id(session) == "logistic_regression_elo_v1"

    # The user deliberately switches back; later startups must respect that.
    model_repo = ModelVersionRepositoryImpl()
    model_repo.activate(session, model_repo.get_by_model_id(session, "decision_tree_v1").id)
    session.commit()
    bootstrap_database(
        engine, session, builtin_dataset_csv=csv_path,
        builtin_model_dirs=[original, elo], default_model_dir=elo,
    )
    assert _active_model_id(session) == "decision_tree_v1"


def test_upgrade_keeps_a_user_trained_active_model(session, tmp_path):
    session, engine = session
    csv_path = _write_csv(tmp_path / "results.csv")
    original, elo = _two_builtin_models(tmp_path)

    bootstrap_database(engine, session, builtin_dataset_csv=csv_path, builtin_model_dirs=[original])
    model_repo = ModelVersionRepositoryImpl()
    builtin_dataset = DatasetRepositoryImpl().get_by_version_label(session, "builtin_v1")
    user_model = model_repo.create(
        session, model_id="logistic_regression_v1", model_type="logistic_regression",
        dataset_id=builtin_dataset.id, feature_version="feature_v1",
        artifact_path=str(tmp_path / "user_model"),
    )
    model_repo.activate(session, user_model.id)
    session.commit()

    bootstrap_database(
        engine, session, builtin_dataset_csv=csv_path,
        builtin_model_dirs=[original, elo], default_model_dir=elo,
    )
    assert _active_model_id(session) == "logistic_regression_v1"
    assert model_repo.get_by_model_id(session, "logistic_regression_elo_v1").is_builtin


def _save_dummy_model(model_dir: Path, model_id: str = "decision_tree_v1") -> None:
    model = make_decision_tree()
    metadata = ModelMetadata(
        model_id=model_id,
        model_type="decision_tree",
        dataset_version="builtin_v1",
        feature_version="feature_v1",
        feature_columns=["f1"],
        tournament_dummy_columns=[],
        cold_start_fill_values={},
        class_labels=["Draw", "Home Loss", "Home Win"],
        training_timestamp="2026-01-01T00:00:00+00:00",
        metrics={},
    )
    import pandas as pd

    model.fit(pd.DataFrame({"f1": [0, 1, 0, 1]}), ["Draw", "Home Win", "Draw", "Home Win"])
    save_model_artifact(model_dir, model, metadata)


def test_concurrent_bootstrap_race_does_not_crash(session, tmp_path, monkeypatch):
    """Regression test for the exact crash found during Stage 5 desktop QA
    (`sqlite3.IntegrityError: UNIQUE constraint failed: datasets.version_label`),
    caused by two processes bootstrapping the same database at once — both
    see no existing row and both try to INSERT it. Simulated here by having
    `DatasetRepositoryImpl.create` raise IntegrityError on its first call
    (as if another process's commit landed between our own check and our
    own insert), with the "winning" row already present in the database —
    exactly what the loser of a real race would see.
    """
    session, engine = session
    dataset_repo = DatasetRepositoryImpl()

    csv_path = _write_csv(tmp_path / "results.csv")

    # Simulate the other (winning) process's commit having already landed.
    winning_row = dataset_repo.create(
        session,
        version_label="builtin_v1",
        name="Built-in Dataset (protected)",
        source="builtin",
        is_builtin=True,
        validation_status="valid",
        row_count=2,
        schema_version="raw_v1",
        file_path=str(csv_path),
    )
    session.commit()

    # Force our own process's insert attempt to fail the way a genuine
    # unique-constraint race would, exactly once.
    original_create = DatasetRepositoryImpl.create
    call_count = {"n": 0}

    def flaky_create(self, session, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            raise IntegrityError("INSERT INTO datasets ...", {}, Exception("UNIQUE constraint failed"))
        return original_create(self, session, **kwargs)

    monkeypatch.setattr(DatasetRepositoryImpl, "create", flaky_create)

    # Bypass the normal "already exists" short-circuit ONCE, to force the
    # exact code path a real race takes: the initial get_by_version_label
    # check returns None (as it would for the losing process, whose check
    # ran before the winner's commit), so bootstrap_database proceeds to
    # _register_builtin_dataset and hits the simulated IntegrityError. The
    # SECOND call is the recovery re-fetch after catching that error, which
    # must see the real (winning) row — exactly as a real re-query would.
    original_get_by_version_label = DatasetRepositoryImpl.get_by_version_label
    lookup_count = {"n": 0}

    def flaky_lookup(self, session, label):
        lookup_count["n"] += 1
        if lookup_count["n"] == 1:
            return None
        return original_get_by_version_label(self, session, label)

    monkeypatch.setattr(DatasetRepositoryImpl, "get_by_version_label", flaky_lookup)

    # Must not raise — the IntegrityError should be caught and recovered
    # from, not crash the whole application startup.
    bootstrap_database(engine, session, builtin_dataset_csv=csv_path)

    monkeypatch.undo()
    all_datasets = dataset_repo.list_all(session)
    assert len(all_datasets) == 1  # never duplicated — the race resolved to one row
    assert all_datasets[0].id == winning_row.id
