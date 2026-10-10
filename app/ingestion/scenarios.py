"""Deterministic synthetic observation scenarios for research and testing."""

from datetime import datetime, timedelta
from enum import Enum

from app.models import DataSource, Observation


class ScenarioKind(str, Enum):
    """Supported synthetic monitoring scenarios."""

    STABLE = "stable"
    DRIFT = "drift"
    POOR_SIGNAL = "poor_signal"
    MISSING_DATA = "missing_data"


def generate_scenario(
    kind: ScenarioKind,
    count: int,
    subject_id: str,
    start_time: datetime,
    interval_seconds: int = 1,
) -> list[Observation]:
    """Generate deterministic synthetic observations for dashboard testing.

    These scenarios are illustrative software test inputs, not clinical
    predictions or evidence of medical detection performance.
    """
    if count <= 0:
        raise ValueError("count must be greater than zero")

    if start_time.tzinfo is None or start_time.utcoffset() is None:
        raise ValueError("start_time must be timezone-aware")

    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be greater than zero")

    if not subject_id.strip():
        raise ValueError("subject_id must not be empty")

    kind = ScenarioKind(kind)
    observations: list[Observation] = []

    for index in range(count):
        heart_rate = 72.0
        spo2 = 98.0
        temperature = 36.7
        activity = "resting"
        signal_quality = 0.95

        if kind == ScenarioKind.STABLE:
            # Small, bounded, repeatable variation.
            heart_rate += (index % 3) - 1
            spo2 -= 0.1 * (index % 2)
            temperature += 0.05 * (index % 2)

        elif kind == ScenarioKind.DRIFT:
            # Illustrative gradual heart-rate drift.
            heart_rate += index * 3.0
            activity = "light_activity"

        elif kind == ScenarioKind.POOR_SIGNAL:
            signal_quality = 0.2 + (index % 3) * 0.1

        elif kind == ScenarioKind.MISSING_DATA:
            # Rotate which measurement is unavailable.
            if index % 3 == 0:
                heart_rate = None
            elif index % 3 == 1:
                spo2 = None
            else:
                temperature = None

        observations.append(
            Observation(
                timestamp=start_time + timedelta(
                    seconds=index * interval_seconds
                ),
                subject_id=subject_id,
                source=DataSource.SCENARIO,
                heart_rate=heart_rate,
                spo2=spo2,
                temperature=temperature,
                activity=activity,
                signal_quality=signal_quality,
                metadata={
                    "scenario": kind.value,
                    "synthetic": True,
                    "sequence": index,
                },
            )
        )

    return observations