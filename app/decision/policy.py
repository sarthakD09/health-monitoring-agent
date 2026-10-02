from app.models import (
    Action,
    AnomalyResult,
    AnomalySeverity,
    Context,
    Decision,
    MonitoringThresholds,
    RiskAssessment,
)


def decide(
    anomaly: AnomalyResult,
    risk: RiskAssessment,
    context: Context,
    thresholds: MonitoringThresholds | None = None,
) -> Decision:
    thresholds = thresholds or MonitoringThresholds()

    if anomaly.severity == AnomalySeverity.UNKNOWN:
        return Decision(
            action=Action.RECHECK,
            reasons=["Evidence is insufficient for reliable monitoring"],
        )

    if anomaly.severity == AnomalySeverity.NORMAL:
        return Decision(
            action=Action.MONITOR,
            reasons=["Observation is within the personal baseline"],
        )

    if anomaly.severity == AnomalySeverity.CRITICAL:
        return Decision(
            action=Action.ESCALATE,
            reasons=[
                "Critical deviation detected",
            ],
        )

    if (
        anomaly.severity == AnomalySeverity.ELEVATED
        and anomaly.consecutive_count >= thresholds.consecutive_deviations_required
    ):
        return Decision(
            action=Action.ESCALATE,
            reasons=[
                "Elevated deviation persisted for the required observations",
            ],
        )

    return Decision(
        action=Action.RECHECK,
        reasons=[
            "Elevated deviation has not persisted long enough",
        ],
    )
