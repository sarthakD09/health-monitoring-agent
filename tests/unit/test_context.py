from app.context.engine import build_context
from app.models import DataSource, Observation


def make_observation(
    activity: str | None = None,
) -> Observation:
    return Observation(
        timestamp="2026-10-02T10:00:00+05:30",
        subject_id="subject-1",
        source=DataSource.SCENARIO,
        heart_rate=70.0,
        signal_quality=0.9,
        activity=activity,
    )


def test_context_contains_activity():
    context = build_context(
        make_observation(activity="walking"),
    )

    assert context.activity == "walking"
    assert context.is_available is True
    assert context.missing_fields == []


def test_missing_activity_is_recorded():
    context = build_context(make_observation())

    assert context.activity is None
    assert context.is_available is False
    assert context.missing_fields == ["activity"]
