from datetime import datetime, timezone

from app.models import Action, DataSource, Observation


def test_observation_schema_accepts_canonical_record():
    obs = Observation(
        timestamp=datetime.now(timezone.utc),
        subject_id="P01",
        source=DataSource.SCENARIO,
        heart_rate=118,
        spo2=97,
        activity="rest",
        signal_quality=0.95,
    )
    assert obs.heart_rate == 118
    assert obs.source == DataSource.SCENARIO
    assert Action.RECHECK.value == "recheck"
