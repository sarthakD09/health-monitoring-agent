import pytest

from app.models import MonitoringThresholds
from app.personalization.baseline import BaselineState, EWMA
from app.storage.sqlite import SQLiteBaselineRepository


def make_state(
    subject_id: str = "subject-1",
    metric: str = "heart_rate",
) -> BaselineState:
    return BaselineState(
        subject_id=subject_id,
        metric=metric,
        mean=70.0,
        variance=0.25,
        count=10,
        alpha=0.1,
        warmup_minimum=3,
    )


def test_save_and_load_baseline(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    state = make_state()

    repository.save(state)

    loaded = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    assert loaded == state


def test_missing_baseline_returns_none(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    loaded = repository.load(
        subject_id="unknown",
        metric="heart_rate",
    )

    assert loaded is None


def test_save_replaces_existing_baseline(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    repository.save(make_state())

    updated = BaselineState(
        subject_id="subject-1",
        metric="heart_rate",
        mean=72.0,
        variance=0.5,
        count=20,
        alpha=0.1,
        warmup_minimum=3,
    )

    repository.save(updated)

    loaded = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    assert loaded == updated


def test_restore_rehydrates_baseline():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    state = BaselineState(
        subject_id="subject-1",
        metric="heart_rate",
        mean=72.0,
        variance=1.5,
        count=12,
        alpha=0.1,
        warmup_minimum=3,
    )

    baseline.restore(state)

    restored = baseline.state

    assert restored == state

def test_restore_rejects_wrong_subject():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    state = BaselineState(
        subject_id="subject-2",
        metric="heart_rate",
        mean=72.0,
        variance=1.5,
        count=12,
        alpha=0.1,
        warmup_minimum=3,
    )

    with pytest.raises(ValueError, match="subject"):
        baseline.restore(state)