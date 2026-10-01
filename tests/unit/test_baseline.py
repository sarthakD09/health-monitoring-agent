from app.personalization.baseline import EWMA
from app.models import DataSource, MonitoringThresholds, Observation


def make_observation(
    heart_rate: float,
    signal_quality: float = 0.9,
    subject_id: str = "subject-1",
) -> Observation:
    return Observation(
        timestamp="2026-10-01T10:00:00+05:30",
        subject_id=subject_id,
        source=DataSource.SCENARIO,
        heart_rate=heart_rate,
        signal_quality=signal_quality,
    )


def test_first_valid_observation_initializes_baseline():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    state = baseline.update(make_observation(70.0))

    assert state.subject_id == "subject-1"
    assert state.metric == "heart_rate"
    assert state.mean == 70.0
    assert state.count == 1


def test_ewma_mean_moves_toward_new_observation():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    baseline.update(make_observation(70.0))
    state = baseline.update(make_observation(80.0))

    assert state.mean == 71.0


def test_baseline_tracks_variance_and_scale():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    baseline.update(make_observation(70.0))
    state = baseline.update(make_observation(80.0))

    assert state.variance >= 0.0
    assert state.scale > 0.0


def test_wrong_subject_is_rejected():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    observation = make_observation(70.0, subject_id="subject-2")

    try:
        baseline.update(observation)
    except ValueError as exc:
        assert "subject" in str(exc).lower()
    else:
        raise AssertionError("Expected subject mismatch to raise ValueError")


def test_insufficient_signal_does_not_update_baseline():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    baseline.update(make_observation(70.0))
    state = baseline.update(make_observation(120.0, signal_quality=0.4))

    assert state.mean == 70.0
    assert state.count == 1


def test_warmup_is_explicit():
    baseline = EWMA(
        subject_id="subject-1",
        metric="heart_rate",
        alpha=0.1,
        warmup_minimum=3,
        thresholds=MonitoringThresholds(),
    )

    baseline.update(make_observation(70.0))
    baseline.update(make_observation(72.0))
    state = baseline.update(make_observation(71.0))

    assert state.count == 3
    assert state.warmup_complete is True


def test_alpha_must_be_between_zero_and_one():
    try:
        EWMA(
            subject_id="subject-1",
            metric="heart_rate",
            alpha=0.0,
            warmup_minimum=3,
            thresholds=MonitoringThresholds(),
        )
    except ValueError as exc:
        assert "alpha" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid alpha to raise ValueError")


def test_warmup_minimum_must_be_positive():
    try:
        EWMA(
            subject_id="subject-1",
            metric="heart_rate",
            alpha=0.1,
            warmup_minimum=0,
            thresholds=MonitoringThresholds(),
        )
    except ValueError as exc:
        assert "warmup" in str(exc).lower()
    else:
        raise AssertionError("Expected invalid warmup_minimum to raise ValueError")
