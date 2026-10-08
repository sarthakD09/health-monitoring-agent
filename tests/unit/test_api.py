from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_process_observation() -> None:
    response = client.post(
        "/observations",
        json={
            "timestamp": "2026-10-09T10:00:00+05:30",
            "subject_id": "subject-api-test",
            "source": "scenario",
            "heart_rate": 70.0,
            "spo2": 98.0,
            "temperature": 36.7,
            "activity": "resting",
            "signal_quality": 0.95,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["observation"]["subject_id"] == "subject-api-test"
    assert body["signal_quality"]["status"] == "trustworthy"
    assert body["decision"]["action"] == "recheck"