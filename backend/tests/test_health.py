"""
Basic tests for the Phase 0 skeleton.

These don't require a live database - the /health endpoint is designed
to report "degraded" rather than crash if the DB is unreachable, so these
tests pass even before .env is configured.
"""

from fastapi.testclient import TestClient

from app.main import app


def test_root():
    with TestClient(app) as client:
        response = client.get("/")

        assert response.status_code == 200

        body = response.json()

        assert body["message"] == "Tomato Disease Advisory Backend"
        assert body["version"] == app.version


def test_health_endpoint_responds():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        body = response.json()
        assert "status" in body
        assert body["status"] in ("ok", "degraded")
