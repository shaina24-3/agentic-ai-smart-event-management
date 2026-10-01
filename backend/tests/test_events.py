import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def get_admin_token(client):
    response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert response.status_code == 200
    return response.json()["access_token"]


def test_get_events(client):
    response = client.get("/api/events")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_event_details(client):
    events_response = client.get("/api/events")

    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0

    event_id = events[0]["id"]

    response = client.get(f"/api/events/{event_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == event_id
    assert "title" in data
    assert "date" in data
    assert "time" in data


def test_create_event(client):
    token = get_admin_token(client)

    response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Test AI Workshop",
            "description": "Testing event creation",
            "date": "2026-12-20",
            "time": "10:00 AM",
            "venue_id": 1,
            "capacity": 50
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["title"] == "Test AI Workshop"
    assert data["capacity"] == 50
    assert "id" in data
def test_update_and_delete_event(client):
    token = get_admin_token(client)

    # 1. Create an event
    create_response = client.post(
        "/api/events",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "CRUD Test Event",
            "description": "Testing update and delete",
            "date": "2026-12-30",
            "time": "10:00 AM",
            "venue_id": 1,
            "capacity": 40
        }
    )

    assert create_response.status_code == 200

    event_id = create_response.json()["id"]

    # 2. Update the event
    update_response = client.put(
        f"/api/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated CRUD Test Event",
            "capacity": 60
        }
    )

    assert update_response.status_code == 200

    updated_event = update_response.json()

    assert updated_event["title"] == "Updated CRUD Test Event"
    assert updated_event["capacity"] == 60

    # 3. Verify the updated event
    get_response = client.get(
        f"/api/events/{event_id}"
    )

    assert get_response.status_code == 200
    assert get_response.json()["title"] == "Updated CRUD Test Event"

    # 4. Delete the event
    delete_response = client.delete(
        f"/api/events/{event_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert delete_response.status_code == 200

    # 5. Verify the event was cancelled
    final_response = client.get(
    f"/api/events/{event_id}"
)

    assert final_response.status_code == 200
    assert final_response.json()["status"] == "CANCELLED"   