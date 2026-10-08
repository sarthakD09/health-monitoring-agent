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

def test_invalid_observation_is_rejected() -> None:
    response = client.post(
        "/observations",
        json={
            "timestamp": "2026-10-09T10:00:00+05:30",
            "subject_id": "subject-invalid",
            "source": "scenario",
            "heart_rate": 70.0,
            "signal_quality": 2.0,
        },
    )

    assert response.status_code == 422

def test_same_subject_reuses_monitoring_service() -> None:
    first = client.post(
        "/observations",
        json={
            "timestamp": "2026-10-09T10:00:00+05:30",
            "subject_id": "subject-reuse-test",
            "source": "scenario",
            "heart_rate": 70.0,
            "signal_quality": 0.95,
        },
    )

    second = client.post(
        "/observations",
        json={
            "timestamp": "2026-10-09T10:01:00+05:30",
            "subject_id": "subject-reuse-test",
            "source": "scenario",
            "heart_rate": 71.0,
            "signal_quality": 0.95,
        },
    )

    assert first.status_code == 200
    assert second.status_code == 200

    assert second.json()["baseline"]["window_size"] == 1

def test_monitor_websocket_processes_observation() -> None:
    with client.websocket_connect("/ws/monitor/ws-test") as websocket:
        websocket.send_json(
            {
                "timestamp": "2026-10-09T10:00:00+05:30",
                "subject_id": "ws-test",
                "source": "scenario",
                "heart_rate": 70.0,
                "spo2": 98.0,
                "temperature": 36.7,
                "activity": "resting",
                "signal_quality": 0.95,
            }
        )

        response = websocket.receive_json()

    assert response["observation"]["subject_id"] == "ws-test"
    assert response["signal_quality"]["status"] == "trustworthy"
    assert response["decision"]["action"] == "recheck"

def test_monitor_websocket_rejects_subject_mismatch() -> None:
    with client.websocket_connect("/ws/monitor/ws-test-mismatch") as websocket:
        websocket.send_json(
            {
                "timestamp": "2026-10-09T10:00:00+05:30",
                "subject_id": "different-subject",
                "source": "scenario",
                "heart_rate": 70.0,
                "signal_quality": 0.95,
            }
        )

        response = websocket.receive_json()

    assert response == {
        "error": "subject_id does not match WebSocket path",
    }