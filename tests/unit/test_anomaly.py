from app.models import (
    AnomalySeverity,
    DataSource,
    MonitoringThresholds,
    Observation,
)
from app.personalization.baseline import BaselineState
from app.anomaly.detector import detect_anomaly


def make_observation(
    heart_rate: float,
    signal_quality: float = 0.9,
    subject_id: str = "subject-1",
) -> Observation:
    return Observation(
        timestamp="2026-10-02T10:00:00+05:30",
        subject_id=subject_id,
        source=DataSource.SCENARIO,
        heart_rate=heart_rate,
        signal_quality=signal_quality,
    )


def make_baseline(
    mean: float = 70.0,
    variance: float = 0.25,
    count: int = 3,
) -> BaselineState:
    return BaselineState(
        subject_id="subject-1",
        metric="heart_rate",
        mean=mean,
        variance=variance,
        count=count,
        alpha=0.1,
        warmup_minimum=3,
    )


def test_normal_observation_is_normal():
    baseline = make_baseline()

    result = detect_anomaly(
        make_observation(70.0),
        baseline,
        MonitoringThresholds(),
    )

    assert result.metric == "heart_rate"
    assert result.severity == AnomalySeverity.NORMAL
    assert result.deviation is not None


def test_elevated_deviation_is_detected():
    baseline = make_baseline()

    result = detect_anomaly(
        make_observation(71.0),
        baseline,
        MonitoringThresholds(),
    )

    assert result.severity == AnomalySeverity.ELEVATED


def test_critical_deviation_is_detected():
    baseline = make_baseline()

    result = detect_anomaly(
        make_observation(75.0),
        baseline,
        MonitoringThresholds(),
    )

    assert result.severity == AnomalySeverity.CRITICAL


def test_consecutive_requirement_prevents_single_elevated_observation_from_escalating():
    baseline = make_baseline()

    thresholds = MonitoringThresholds(
        consecutive_deviations_required=2,
    )

    result = detect_anomaly(
        make_observation(71.0),
        baseline,
        thresholds,
        consecutive_count=1,
    )

    assert result.severity == AnomalySeverity.ELEVATED
    assert result.consecutive_count == 1


def test_consecutive_requirement_is_recorded():
    baseline = make_baseline()

    thresholds = MonitoringThresholds(
        consecutive_deviations_required=2,
    )

    result = detect_anomaly(
        make_observation(71.0),
        baseline,
        thresholds,
        consecutive_count=2,
    )

    assert result.consecutive_count == 2


def test_insufficient_signal_produces_unknown_anomaly():
    baseline = make_baseline()

    result = detect_anomaly(
        make_observation(75.0, signal_quality=0.4),
        baseline,
        MonitoringThresholds(),
    )

    assert result.severity == AnomalySeverity.UNKNOWN
    assert result.deviation is None


def test_warmup_baseline_produces_unknown_anomaly():
    baseline = make_baseline(count=1)
    result = detect_anomaly(
        make_observation(75.0),
        baseline,
        MonitoringThresholds(),
    )

    assert result.severity == AnomalySeverity.UNKNOWN
