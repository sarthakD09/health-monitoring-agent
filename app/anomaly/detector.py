from app.models import (
    AnomalyResult,
    AnomalySeverity,
    MonitoringThresholds,
    Observation,
)
from app.personalization.baseline import BaselineState


def detect_anomaly(
    observation: Observation,
    baseline: BaselineState,
    thresholds: MonitoringThresholds,
    consecutive_count: int = 1,
) -> AnomalyResult:
    if observation.subject_id != baseline.subject_id:
        raise ValueError("observation subject does not match baseline subject")

    value = getattr(observation, baseline.metric, None)

    if value is None:
        raise ValueError(
            f"observation does not contain metric: {baseline.metric}"
        )

    if (
        observation.signal_quality is None
        or observation.signal_quality < thresholds.signal_quality_minimum
    ):
        return AnomalyResult(
            metric=baseline.metric,
            severity=AnomalySeverity.UNKNOWN,
            deviation=None,
            consecutive_count=consecutive_count,
            reasons=["Signal quality is insufficient"],
        )

    if not baseline.warmup_complete:
        return AnomalyResult(
            metric=baseline.metric,
            severity=AnomalySeverity.UNKNOWN,
            deviation=None,
            consecutive_count=consecutive_count,
            reasons=["Personal baseline is still warming up"],
        )

    deviation = abs(value - baseline.mean) / baseline.scale

    if deviation >= thresholds.critical_deviation:
        severity = AnomalySeverity.CRITICAL
    elif deviation >= thresholds.elevated_deviation:
        severity = AnomalySeverity.ELEVATED
    else:
        severity = AnomalySeverity.NORMAL

    return AnomalyResult(
        metric=baseline.metric,
        severity=severity,
        deviation=deviation,
        consecutive_count=consecutive_count,
        reasons=[
            f"Deviation from personal baseline is "
            f"{deviation:.2f} standard deviations"
        ],
    )