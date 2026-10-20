"""Health API tests."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_info() -> None:
    response = client.get("/api/health/info")
    assert response.status_code == 200
    assert response.json() == {"app": "BookMyShow", "status": "ok"}
