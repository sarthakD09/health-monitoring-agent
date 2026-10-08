from app.application.monitoring import MonitoringService
from app.models import (
    Action,
    DataSource,
    Observation,
)


def make_observation(
    heart_rate: float,
    signal_quality: float = 0.9,
    activity: str | None = "resting",
) -> Observation:
    return Observation(
        timestamp="2026-10-02T10:00:00+05:30",
        subject_id="subject-1",
        source=DataSource.SCENARIO,
        heart_rate=heart_rate,
        signal_quality=signal_quality,
        activity=activity,
    )


def test_service_starts_with_recheck_during_baseline_warmup():
    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
    )

    result = service.process(
        make_observation(70.0),
    )

    assert result.decision.action == Action.RECHECK
    assert result.anomaly.severity.value == "unknown"


def test_service_builds_baseline_after_valid_observations():
    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
    )

    service.process(make_observation(70.0))
    service.process(make_observation(70.0))

    result = service.process(
        make_observation(70.0),
    )

    assert result.baseline is not None
    assert result.baseline.window_size == 2


def test_normal_observation_is_monitored_after_warmup():
    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
    )

    service.process(make_observation(70.0))
    service.process(make_observation(70.0))
    service.process(make_observation(70.0))

    result = service.process(
        make_observation(70.0),
    )

    assert result.anomaly.severity.value == "normal"
    assert result.decision.action == Action.MONITOR


def test_poor_signal_causes_recheck():
    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
    )

    service.process(make_observation(70.0))
    service.process(make_observation(70.0))
    service.process(make_observation(70.0))

    result = service.process(
        make_observation(
            90.0,
            signal_quality=0.3,
        ),
    )

    assert result.decision.action == Action.RECHECK

def test_anomalous_observation_does_not_update_baseline():
    service = MonitoringService(
        subject_id="subject-1",
        warmup_minimum=3,
    )

    service.process(make_observation(70.0))
    service.process(make_observation(70.0))
    service.process(make_observation(70.0))

    before = service.baseline.state

    result = service.process(
        make_observation(90.0),
    )

    after = service.baseline.state

    assert result.anomaly.severity.value == "critical"
    assert after.count == before.count
    assert after.mean == before.mean
    assert after.variance == before.variance