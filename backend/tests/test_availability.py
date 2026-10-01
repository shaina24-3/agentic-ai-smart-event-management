import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def create_user(client):
    email = f"capacity_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Capacity Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert response.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={
            "name": "Capacity Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login.status_code == 200

    return login.json()["access_token"]


def get_event(client):
    response = client.get("/api/events")

    assert response.status_code == 200

    events = response.json()
    assert len(events) > 0

    return events[0]


def test_event_has_capacity_information(client):
    event = get_event(client)

    assert "capacity" in event
    assert event["capacity"] > 0


def test_user_can_register_when_event_has_capacity(client):
    token = create_user(client)
    event = get_event(client)

    response = client.post(
        f"/api/events/{event['id']}/register",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
def test_registration_blocked_when_capacity_reached(client):
    import uuid

    # Login as admin
    admin_login = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert admin_login.status_code == 200
    admin_token = admin_login.json()["access_token"]

    # Create a test event with capacity 1
    create_response = client.post(
        "/api/events",
        headers={
            "Authorization": f"Bearer {admin_token}"
        },
        json={
            "title": "Capacity Limit Test",
            "description": "Testing event capacity",
            "date": "2027-01-10",
            "time": "10:00 AM",
            "venue_id": 1,
            "capacity": 1
        }
    )

    assert create_response.status_code == 200
    event_id = create_response.json()["id"]

    # Create first user
    email1 = f"capacity1_{uuid.uuid4().hex[:8]}@example.com"

    register1 = client.post(
        "/api/auth/register",
        json={
            "name": "Capacity User One",
            "email": email1,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register1.status_code == 200

    login1 = client.post(
        "/api/auth/login",
        json={
            "name": "Capacity User One",
            "email": email1,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login1.status_code == 200
    token1 = login1.json()["access_token"]

    # First user registers successfully
    first_registration = client.post(
        f"/api/events/{event_id}/register",
        headers={
            "Authorization": f"Bearer {token1}"
        }
    )

    assert first_registration.status_code == 200

    # Create second user
    email2 = f"capacity2_{uuid.uuid4().hex[:8]}@example.com"

    register2 = client.post(
        "/api/auth/register",
        json={
            "name": "Capacity User Two",
            "email": email2,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register2.status_code == 200

    login2 = client.post(
        "/api/auth/login",
        json={
            "name": "Capacity User Two",
            "email": email2,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login2.status_code == 200
    token2 = login2.json()["access_token"]

    # Second user should be rejected because capacity is full
    second_registration = client.post(
        f"/api/events/{event_id}/register",
        headers={
            "Authorization": f"Bearer {token2}"
        }
    )

    assert second_registration.status_code == 400
    assert "capacity" in second_registration.json()["detail"].lower()    