from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.models import (
    Action,
    AnomalyResult,
    AnomalySeverity,
    Baseline,
    Context,
    DataSource,
    Decision,
    MonitoringResult,
    MonitoringThresholds,
    Observation,
    RiskAssessment,
    SignalQuality,
    SignalQualityStatus,
)


def test_observation_rejects_naive_timestamp() -> None:
    """A source record without an offset cannot be ordered safely across sources."""
    with pytest.raises(ValidationError, match="timezone-aware"):
        Observation(
            timestamp=datetime(2026, 9, 24, 9, 0),
            subject_id="P01",
            source=DataSource.SCENARIO,
            heart_rate=70,
        )


@pytest.mark.parametrize("signal_quality", [-0.01, 1.01])
def test_observation_rejects_signal_quality_outside_unit_interval(
    signal_quality: float,
) -> None:
    """Adapters must not turn invalid quality values into trusted evidence."""
    with pytest.raises(ValidationError):
        Observation(
            timestamp=datetime(2026, 9, 24, 9, 0, tzinfo=timezone.utc),
            subject_id="P01",
            source=DataSource.SCENARIO,
            heart_rate=70,
            signal_quality=signal_quality,
        )


def test_monitoring_result_keeps_risk_separate_from_final_decision() -> None:
    """Changing evidence must not itself choose the final allowed system state."""
    observation = Observation(
        timestamp=datetime(2026, 9, 24, 9, 0, tzinfo=timezone.utc),
        subject_id="P01",
        source=DataSource.SCENARIO,
        heart_rate=118,
        activity="rest",
        signal_quality=0.95,
    )
    result = MonitoringResult(
        observation=observation,
        signal_quality=SignalQuality(
            status=SignalQualityStatus.TRUSTWORTHY,
            score=0.95,
            reasons=["Scenario quality is within the configured range."],
        ),
        baseline=Baseline(
            subject_id="P01",
            metric="heart_rate",
            center=70,
            scale=10,
            window_size=30,
        ),
        anomaly=AnomalyResult(
            metric="heart_rate",
            severity=AnomalySeverity.ELEVATED,
            deviation=4.8,
            consecutive_count=2,
            reasons=["Heart rate is elevated relative to the personal baseline."],
        ),
        context=Context(activity="rest"),
        risk=RiskAssessment(
            score=0.8,
            severity=AnomalySeverity.ELEVATED,
            reasons=["Reliable elevated deviation evidence is present."],
        ),
        decision=Decision(
            action=Action.RECHECK,
            reasons=["A deterministic policy requires another measurement."],
        ),
    )

    assert result.risk.score == 0.8
    assert result.decision.action is Action.RECHECK


def test_risk_assessment_rejects_a_final_action() -> None:
    """Policy, rather than risk assessment, owns the final action field."""
    with pytest.raises(ValidationError, match="action"):
        RiskAssessment(
            score=0.8,
            severity=AnomalySeverity.ELEVATED,
            action=Action.ESCALATE,
        )


def test_monitoring_thresholds_reject_inconsistent_or_out_of_range_values() -> None:
    """Demo thresholds remain typed configuration rather than unchecked constants."""
    with pytest.raises(ValidationError):
        MonitoringThresholds(signal_quality_minimum=1.01)

    with pytest.raises(ValidationError, match="critical"):
        MonitoringThresholds(elevated_deviation=3.0, critical_deviation=2.0)
