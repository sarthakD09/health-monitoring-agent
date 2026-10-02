from app.decision.policy import decide
from app.models import (
    Action,
    AnomalyResult,
    AnomalySeverity,
    Context,
    RiskAssessment,
)


def make_context() -> Context:
    return Context(
        activity="resting",
        is_available=True,
    )


def make_risk(
    severity: AnomalySeverity,
) -> RiskAssessment:
    score = {
        AnomalySeverity.UNKNOWN: 0.0,
        AnomalySeverity.NORMAL: 0.0,
        AnomalySeverity.ELEVATED: 0.5,
        AnomalySeverity.CRITICAL: 1.0,
    }[severity]

    return RiskAssessment(
        score=score,
        severity=severity,
        reasons=[],
        missing_context=[],
    )


def make_anomaly(
    severity: AnomalySeverity,
    consecutive_count: int = 1,
) -> AnomalyResult:
    return AnomalyResult(
        metric="heart_rate",
        severity=severity,
        deviation=None,
        consecutive_count=consecutive_count,
        reasons=[],
    )


def test_unknown_signal_rechecks():
    decision = decide(
        make_anomaly(AnomalySeverity.UNKNOWN),
        make_risk(AnomalySeverity.UNKNOWN),
        make_context(),
    )

    assert decision.action == Action.RECHECK


def test_normal_evidence_monitors():
    decision = decide(
        make_anomaly(AnomalySeverity.NORMAL),
        make_risk(AnomalySeverity.NORMAL),
        make_context(),
    )

    assert decision.action == Action.MONITOR


def test_single_elevated_observation_rechecks():
    decision = decide(
        make_anomaly(
            AnomalySeverity.ELEVATED,
            consecutive_count=1,
        ),
        make_risk(AnomalySeverity.ELEVATED),
        make_context(),
    )

    assert decision.action == Action.RECHECK


def test_persistent_elevated_observation_escalates():
    decision = decide(
        make_anomaly(
            AnomalySeverity.ELEVATED,
            consecutive_count=2,
        ),
        make_risk(AnomalySeverity.ELEVATED),
        make_context(),
    )

    assert decision.action == Action.ESCALATE


def test_critical_evidence_escalates():
    decision = decide(
        make_anomaly(
            AnomalySeverity.CRITICAL,
            consecutive_count=1,
        ),
        make_risk(AnomalySeverity.CRITICAL),
        make_context(),
    )

    assert decision.action == Action.ESCALATE
