from app.models import (
    AnomalyResult,
    AnomalySeverity,
    Context,
    RiskAssessment,
)


def assess_risk(
    anomaly: AnomalyResult,
    context: Context,
) -> RiskAssessment:
    reasons = list(anomaly.reasons)

    if anomaly.severity == AnomalySeverity.UNKNOWN:
        reasons.append("Risk cannot be determined reliably from current evidence")

        return RiskAssessment(
            score=0.0,
            severity=AnomalySeverity.UNKNOWN,
            reasons=reasons,
            missing_context=context.missing_fields,
        )

    if anomaly.severity == AnomalySeverity.NORMAL:
        score = 0.0

    elif anomaly.severity == AnomalySeverity.ELEVATED:
        score = 0.5

    else:
        score = 1.0

    if context.activity is not None:
        reasons.append(f"Observed activity context: {context.activity}")

    return RiskAssessment(
        score=score,
        severity=anomaly.severity,
        reasons=reasons,
        missing_context=context.missing_fields,
    )
