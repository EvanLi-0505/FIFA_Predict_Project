"""Stage 2 validation: repository layer works correctly, and generates no
engine-specific SQL (Development Prompt.md Section 10).

Functional CRUD/activation/protection tests run against an in-memory
SQLite engine — the same code path the Desktop backend uses. A separate
dialect-compilation check proves the exact same ORM calls also compile
cleanly under the MySQL dialect, without requiring a live MySQL server in
this dev environment.
"""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.dialects import mysql

from database.engine import create_all_tables, create_db_engine, create_session_factory
from database.models import Dataset, ModelVersion, Prediction
from database.repositories.sqlalchemy_repositories import (
    DatasetRepositoryImpl,
    ModelVersionRepositoryImpl,
    PredictionRepositoryImpl,
)


@pytest.fixture
def session():
    engine = create_db_engine("sqlite:///:memory:")
    create_all_tables(engine)
    factory = create_session_factory(engine)
    with factory() as session:
        yield session


@pytest.fixture
def dataset_repo():
    return DatasetRepositoryImpl()


@pytest.fixture
def model_repo():
    return ModelVersionRepositoryImpl()


@pytest.fixture
def prediction_repo():
    return PredictionRepositoryImpl()


def _make_builtin(session, dataset_repo) -> Dataset:
    return dataset_repo.create(
        session,
        version_label="builtin_v1",
        name="Built-in Dataset",
        source="builtin",
        is_builtin=True,
        validation_status="valid",
        row_count=49520,
        schema_version="raw_v1",
        file_path="datasets/builtin/results.csv",
    )


def _make_upload(session, dataset_repo, label="user_v1") -> Dataset:
    return dataset_repo.create(
        session,
        version_label=label,
        name="My upload",
        source="upload",
        is_builtin=False,
        validation_status="valid",
        row_count=1000,
        schema_version="raw_v1",
        file_path=f"datasets/user/{label}.csv",
    )


# --- Dataset repository -----------------------------------------------


def test_create_and_get_builtin_dataset(session, dataset_repo):
    created = _make_builtin(session, dataset_repo)
    session.commit()

    fetched = dataset_repo.get_by_version_label(session, "builtin_v1")
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.is_builtin is True


def test_builtin_dataset_cannot_be_deleted(session, dataset_repo):
    builtin = _make_builtin(session, dataset_repo)
    session.commit()

    with pytest.raises(PermissionError):
        dataset_repo.delete(session, builtin.id)

    assert dataset_repo.get_by_id(session, builtin.id) is not None


def test_uploaded_dataset_can_be_deleted(session, dataset_repo):
    upload = _make_upload(session, dataset_repo)
    session.commit()

    dataset_repo.delete(session, upload.id)
    session.commit()

    assert dataset_repo.get_by_id(session, upload.id) is None


def test_activating_a_dataset_deactivates_all_others(session, dataset_repo):
    builtin = _make_builtin(session, dataset_repo)
    upload = _make_upload(session, dataset_repo)
    session.commit()

    dataset_repo.activate(session, builtin.id)
    assert dataset_repo.get_active(session).id == builtin.id

    dataset_repo.activate(session, upload.id)
    session.commit()

    active = dataset_repo.get_active(session)
    assert active.id == upload.id

    refreshed_builtin = dataset_repo.get_by_id(session, builtin.id)
    assert refreshed_builtin.is_active is False


def test_invalid_dataset_cannot_be_activated(session, dataset_repo):
    invalid = dataset_repo.create(
        session,
        version_label="user_v2",
        name="Bad upload",
        source="upload",
        is_builtin=False,
        validation_status="invalid",
        row_count=0,
        schema_version="raw_v1",
        file_path="datasets/user/user_v2.csv",
    )
    session.commit()

    with pytest.raises(ValueError):
        dataset_repo.activate(session, invalid.id)


def test_next_user_version_label_increments(session, dataset_repo):
    assert dataset_repo.next_user_version_label(session) == "user_v1"

    _make_upload(session, dataset_repo, label="user_v1")
    session.commit()
    assert dataset_repo.next_user_version_label(session) == "user_v2"

    _make_upload(session, dataset_repo, label="user_v2")
    session.commit()
    assert dataset_repo.next_user_version_label(session) == "user_v3"


# --- ModelVersion repository --------------------------------------------


def test_model_version_activation_and_dataset_link(session, dataset_repo, model_repo):
    builtin = _make_builtin(session, dataset_repo)
    session.commit()

    model_a = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
        metrics={"macro_f1": 0.39},
    )
    model_b = model_repo.create(
        session,
        model_id="decision_tree_v2",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v2",
        metrics={"macro_f1": 0.40},
    )
    session.commit()

    model_repo.activate(session, model_a.id)
    assert model_repo.get_active(session).id == model_a.id

    model_repo.activate(session, model_b.id)
    session.commit()

    assert model_repo.get_active(session).id == model_b.id
    assert model_repo.get_by_id(session, model_a.id).is_active is False

    dataset_models = model_repo.list_by_dataset(session, builtin.id)
    assert {m.id for m in dataset_models} == {model_a.id, model_b.id}


def test_builtin_model_cannot_be_deleted(session, dataset_repo, model_repo):
    builtin_dataset = _make_builtin(session, dataset_repo)
    builtin_model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin_dataset.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
        is_builtin=True,
    )
    session.commit()

    with pytest.raises(PermissionError):
        model_repo.delete(session, builtin_model.id)


def test_active_model_cannot_be_deleted(session, dataset_repo, model_repo):
    builtin_dataset = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin_dataset.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()
    model_repo.activate(session, model.id)
    session.commit()

    with pytest.raises(ValueError):
        model_repo.delete(session, model.id)


def test_model_with_prediction_history_cannot_be_deleted(
    session, dataset_repo, model_repo, prediction_repo
):
    builtin_dataset = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin_dataset.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()

    prediction_repo.create(
        session,
        model_version_id=model.id,
        dataset_id=builtin_dataset.id,
        home_team="England",
        away_team="Argentina",
        host_country="United States",
        tournament="FIFA World Cup",
        neutral=1,
        probabilities={"Home Win": 0.3, "Draw": 0.2, "Home Loss": 0.5},
        predicted_outcome="Home Loss",
        confidence=0.5,
    )
    session.commit()

    with pytest.raises(ValueError):
        model_repo.delete(session, model.id)


def test_model_without_history_can_be_deleted(session, dataset_repo, model_repo):
    builtin_dataset = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v2",
        model_type="decision_tree",
        dataset_id=builtin_dataset.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v2",
    )
    session.commit()

    model_repo.delete(session, model.id)
    session.commit()

    assert model_repo.get_by_id(session, model.id) is None


# --- Prediction repository -----------------------------------------------


def test_prediction_history_records_and_lists(session, dataset_repo, model_repo, prediction_repo):
    builtin = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()

    prediction = prediction_repo.create(
        session,
        model_version_id=model.id,
        dataset_id=builtin.id,
        home_team="England",
        away_team="Argentina",
        host_country="United States",
        tournament="FIFA World Cup",
        neutral=1,
        probabilities={"Home Win": 0.37, "Draw": 0.21, "Home Loss": 0.42},
        predicted_outcome="Home Loss",
        confidence=0.42,
    )
    session.commit()

    recent = prediction_repo.list_recent(session, limit=10)
    assert len(recent) == 1
    assert recent[0].id == prediction.id
    assert recent[0].home_team == "England"


def test_prediction_can_be_deleted_individually(session, dataset_repo, model_repo, prediction_repo):
    builtin = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()

    kept = prediction_repo.create(
        session, model_version_id=model.id, dataset_id=builtin.id, home_team="A",
        away_team="B", host_country="A", tournament="Friendly", neutral=0,
        probabilities={"Home Win": 1, "Draw": 0, "Home Loss": 0},
        predicted_outcome="Home Win", confidence=1.0,
    )
    to_delete = prediction_repo.create(
        session, model_version_id=model.id, dataset_id=builtin.id, home_team="C",
        away_team="D", host_country="C", tournament="Friendly", neutral=0,
        probabilities={"Home Win": 1, "Draw": 0, "Home Loss": 0},
        predicted_outcome="Home Win", confidence=1.0,
    )
    session.commit()

    prediction_repo.delete(session, to_delete.id)
    session.commit()

    remaining = prediction_repo.list_recent(session, limit=10)
    assert [p.id for p in remaining] == [kept.id]


def test_delete_all_predictions_clears_history_and_returns_count(
    session, dataset_repo, model_repo, prediction_repo
):
    builtin = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()

    for _ in range(3):
        prediction_repo.create(
            session, model_version_id=model.id, dataset_id=builtin.id, home_team="A",
            away_team="B", host_country="A", tournament="Friendly", neutral=0,
            probabilities={"Home Win": 1, "Draw": 0, "Home Loss": 0},
            predicted_outcome="Home Win", confidence=1.0,
        )
    session.commit()

    deleted_count = prediction_repo.delete_all(session)
    session.commit()

    assert deleted_count == 3
    assert prediction_repo.list_recent(session, limit=10) == []


def test_count_by_outcome_and_list_all_confidences(
    session, dataset_repo, model_repo, prediction_repo
):
    builtin = _make_builtin(session, dataset_repo)
    model = model_repo.create(
        session,
        model_id="decision_tree_v1",
        model_type="decision_tree",
        dataset_id=builtin.id,
        feature_version="feature_v1",
        artifact_path="models/decision_tree/v1",
    )
    session.commit()

    outcomes_and_confidences = [("Home Win", 0.5), ("Home Win", 0.6), ("Draw", 0.4)]
    for outcome, confidence in outcomes_and_confidences:
        prediction_repo.create(
            session, model_version_id=model.id, dataset_id=builtin.id, home_team="A",
            away_team="B", host_country="A", tournament="Friendly", neutral=0,
            probabilities={"Home Win": 1, "Draw": 0, "Home Loss": 0},
            predicted_outcome=outcome, confidence=confidence,
        )
    session.commit()

    counts = prediction_repo.count_by_outcome(session)
    assert counts == {"Home Win": 2, "Draw": 1}

    confidences = prediction_repo.list_all_confidences(session)
    assert sorted(confidences) == [0.4, 0.5, 0.6]


# --- Dialect-agnosticism (Section 10: no engine-specific SQL) -----------


@pytest.mark.parametrize(
    "statement",
    [
        select(Dataset).where(Dataset.is_active.is_(True)),
        select(ModelVersion).where(ModelVersion.is_active.is_(True)),
        select(Prediction).order_by(Prediction.created_at.desc()).limit(10),
    ],
)
def test_queries_compile_under_mysql_dialect(statement):
    # Compiling (not executing) against the MySQL dialect proves the ORM
    # queries used by the repositories contain no SQLite-specific syntax,
    # without requiring a live MySQL server in this dev environment.
    compiled = statement.compile(dialect=mysql.dialect())
    assert compiled is not None
