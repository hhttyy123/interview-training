from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_session_can_start_and_stop_over_websocket() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/voice") as websocket:
        websocket.send_json({"type": "session.start"})
        ready = websocket.receive_json()
        assert ready["type"] == "session.ready"
        assert ready["session_id"]

        websocket.send_json({"type": "session.stop"})
        ended = websocket.receive_json()
        assert ended == {"type": "session.ended", "session_id": ready["session_id"]}


def test_malformed_websocket_json_returns_session_error() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/voice") as websocket:
        websocket.send_text("{")
        error = websocket.receive_json()
        assert error == {"type": "session.error", "message": "Malformed session event JSON."}
