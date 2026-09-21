from app.models import Action, RiskAssessment


def validate_action(assessment: RiskAssessment) -> RiskAssessment:
    """Apply deterministic safety constraints to a proposed risk state."""
    if assessment.action not in {Action.MONITOR, Action.RECHECK, Action.ESCALATE}:
        raise ValueError(f"Unsupported action: {assessment.action}")
    return assessment
