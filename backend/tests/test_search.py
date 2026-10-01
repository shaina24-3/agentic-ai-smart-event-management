import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def test_search_existing_event(client):
    response = client.get(
        "/api/events",
        params={"keyword": "AI"}
    )

    assert response.status_code == 200

    events = response.json()

    assert isinstance(events, list)
    assert len(events) > 0

    for event in events:
        assert "ai" in event["title"].lower()


def test_search_non_existing_event(client):
    response = client.get(
        "/api/events",
        params={"keyword": "XYZNonExistingEvent"}
    )

    assert response.status_code == 200

    events = response.json()

    assert isinstance(events, list)
    assert len(events) == 0