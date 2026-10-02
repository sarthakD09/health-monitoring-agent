from app.context.engine import build_context
from app.models import (
    AnomalyResult,
    AnomalySeverity,
    DataSource,
    Observation,
)
from app.risk.assessment import assess_risk


def make_observation(
    activity: str | None = None,
) -> Observation:
    return Observation(
        timestamp="2026-10-02T10:00:00+05:30",
        subject_id="subject-1",
        source=DataSource.SCENARIO,
        heart_rate=70.0,
        signal_quality=0.9,
        activity=activity,
    )


def test_normal_anomaly_produces_low_risk():
    anomaly = AnomalyResult(
        metric="heart_rate",
        severity=AnomalySeverity.NORMAL,
        deviation=0.5,
        consecutive_count=1,
        reasons=["Within personal baseline"],
    )

    context = build_context(
        make_observation(activity="resting"),
    )

    risk = assess_risk(anomaly, context)

    assert risk.severity == AnomalySeverity.NORMAL
    assert risk.score == 0.0
    assert risk.missing_context == []


def test_elevated_anomaly_produces_elevated_risk():
    anomaly = AnomalyResult(
        metric="heart_rate",
        severity=AnomalySeverity.ELEVATED,
        deviation=2.2,
        consecutive_count=1,
        reasons=["Elevated deviation"],
    )

    context = build_context(
        make_observation(activity="walking"),
    )

    risk = assess_risk(anomaly, context)

    assert risk.severity == AnomalySeverity.ELEVATED
    assert risk.score > 0.0


def test_critical_anomaly_produces_high_risk():
    anomaly = AnomalyResult(
        metric="heart_rate",
        severity=AnomalySeverity.CRITICAL,
        deviation=4.0,
        consecutive_count=2,
        reasons=["Critical deviation"],
    )

    context = build_context(
        make_observation(activity="resting"),
    )

    risk = assess_risk(anomaly, context)

    assert risk.severity == AnomalySeverity.CRITICAL
    assert risk.score == 1.0


def test_unknown_anomaly_preserves_uncertainty():
    anomaly = AnomalyResult(
        metric="heart_rate",
        severity=AnomalySeverity.UNKNOWN,
        deviation=None,
        consecutive_count=0,
        reasons=["Signal quality is insufficient"],
    )

    context = build_context(make_observation())

    risk = assess_risk(anomaly, context)

    assert risk.severity == AnomalySeverity.UNKNOWN
    assert risk.score == 0.0
