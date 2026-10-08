from app.application.monitoring import MonitoringService
from app.models import DataSource, Observation
from app.storage.sqlite import SQLiteBaselineRepository


def make_observation(
    heart_rate: float,
    signal_quality: float = 0.9,
) -> Observation:
    return Observation(
        timestamp="2026-10-02T10:00:00+05:30",
        subject_id="subject-1",
        source=DataSource.SCENARIO,
        heart_rate=heart_rate,
        signal_quality=signal_quality,
        activity="resting",
    )


def test_monitoring_service_persists_baseline(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
        baseline_repository=repository,
    )

    service.process(make_observation(70.0))

    persisted = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    assert persisted is not None
    assert persisted.count == 1
    assert persisted.mean == 70.0


def test_monitoring_service_restores_persisted_baseline(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    service1 = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
        baseline_repository=repository,
    )

    service1.process(make_observation(70.0))
    service1.process(make_observation(72.0))

    persisted = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    assert persisted is not None

    service2 = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
        baseline_repository=repository,
    )

    restored = service2.baseline.state

    assert restored == persisted


def test_anomalous_observation_is_not_persisted(tmp_path):
    repository = SQLiteBaselineRepository(
        tmp_path / "health_monitoring.db",
    )

    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
        baseline_repository=repository,
    )

    service.process(make_observation(70.0))
    service.process(make_observation(70.0))
    service.process(make_observation(70.0))

    before = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    result = service.process(
        make_observation(90.0),
    )

    after = repository.load(
        subject_id="subject-1",
        metric="heart_rate",
    )

    assert result.anomaly.severity.value == "critical"
    assert before == after
