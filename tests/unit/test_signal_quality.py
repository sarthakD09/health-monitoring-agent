

from app.models import DataSource, Observation, SignalQualityStatus
from app.signal.quality import evaluate_signal_quality


def make_observation(signal_quality: float | None) -> Observation:
    return Observation(
        timestamp="2026-09-30T10:00:00+05:30",
        subject_id="subject-1",
        source=DataSource.SCENARIO,
        heart_rate=72.0,
        signal_quality=signal_quality,
    )


def test_trustworthy_signal_is_accepted():
    observation = make_observation(0.9)

    result = evaluate_signal_quality(observation)

    assert result.status == SignalQualityStatus.TRUSTWORTHY
    assert result.score == 0.9


def test_signal_at_minimum_threshold_is_trustworthy():
    observation = make_observation(0.7)

    result = evaluate_signal_quality(observation)

    assert result.status == SignalQualityStatus.TRUSTWORTHY


def test_signal_below_minimum_is_insufficient():
    observation = make_observation(0.6)

    result = evaluate_signal_quality(observation)

    assert result.status == SignalQualityStatus.INSUFFICIENT
    assert result.score == 0.6


def test_missing_signal_quality_is_insufficient():
    observation = make_observation(None)

    result = evaluate_signal_quality(observation)

    assert result.status == SignalQualityStatus.INSUFFICIENT
    assert result.score is None


def test_insufficient_signal_contains_reason():
    observation = make_observation(0.4)

    result = evaluate_signal_quality(observation)

    assert result.status == SignalQualityStatus.INSUFFICIENT
    assert result.reasons