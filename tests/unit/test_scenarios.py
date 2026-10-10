
from datetime import datetime, timedelta, timezone

import pytest

from app.ingestion.scenarios import ScenarioKind, generate_scenario


def test_stable_scenario_is_deterministic():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    first = generate_scenario(
        ScenarioKind.STABLE,
        count=5,
        subject_id="test-subject",
        start_time=start,
    )
    second = generate_scenario(
        ScenarioKind.STABLE,
        count=5,
        subject_id="test-subject",
        start_time=start,
    )

    assert first == second
    assert len(first) == 5
    assert all(item.source.value == "scenario" for item in first)


def test_scenario_timestamps_are_timezone_aware_and_ordered():
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)

    observations = generate_scenario(
        ScenarioKind.STABLE,
        count=4,
        subject_id="test-subject",
        start_time=start,
        interval_seconds=2,
    )

    assert [item.timestamp for item in observations] == [
        start + timedelta(seconds=2 * index)
        for index in range(4)
    ]


def test_drift_scenario_changes_heart_rate_gradually():
    observations = generate_scenario(
        ScenarioKind.DRIFT,
        count=5,
        subject_id="test-subject",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    heart_rates = [item.heart_rate for item in observations]

    assert all(value is not None for value in heart_rates)
    assert heart_rates == sorted(heart_rates)
    assert len(set(heart_rates)) > 1


def test_poor_signal_scenario_has_low_quality_scores():
    observations = generate_scenario(
        ScenarioKind.POOR_SIGNAL,
        count=3,
        subject_id="test-subject",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert all(
        item.signal_quality is not None and item.signal_quality < 0.5
        for item in observations
    )


def test_missing_data_scenario_contains_missing_measurements():
    observations = generate_scenario(
        ScenarioKind.MISSING_DATA,
        count=4,
        subject_id="test-subject",
        start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )

    assert any(
        item.heart_rate is None
        or item.spo2 is None
        or item.temperature is None
        for item in observations
    )


@pytest.mark.parametrize("count", [0, -1])
def test_invalid_count_is_rejected(count):
    with pytest.raises(ValueError, match="count"):
        generate_scenario(
            ScenarioKind.STABLE,
            count=count,
            subject_id="test-subject",
            start_time=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )


def test_naive_start_time_is_rejected():
    with pytest.raises(ValueError, match="timezone-aware"):
        generate_scenario(
            ScenarioKind.STABLE,
            count=2,
            subject_id="test-subject",
            start_time=datetime(2026, 1, 1),
        )
