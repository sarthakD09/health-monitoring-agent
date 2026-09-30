from app.models import (
    Observation,
    MonitoringThresholds,
    SignalQuality,
    SignalQualityStatus,
)


def evaluate_signal_quality(
    observation: Observation,
    thresholds: MonitoringThresholds | None = None,
) -> SignalQuality:
    """Evaluate whether an observation has sufficient signal quality."""
    thresholds = thresholds or MonitoringThresholds()
    score = observation.signal_quality

    if score is None:
        return SignalQuality(
            status=SignalQualityStatus.INSUFFICIENT,
            score=None,
            reasons=["Signal quality is unavailable"],
        )

    if score < thresholds.signal_quality_minimum:
        return SignalQuality(
            status=SignalQualityStatus.INSUFFICIENT,
            score=score,
            reasons=[
                "Signal quality is below the configured minimum",
            ],
        )

    return SignalQuality(
        status=SignalQualityStatus.TRUSTWORTHY,
        score=score,
        reasons=["Signal quality is sufficient"],
    )