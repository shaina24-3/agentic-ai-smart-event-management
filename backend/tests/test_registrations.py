import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


def create_test_user(client):
    email = f"registration_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Registration Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Registration Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login_response.status_code == 200

    return login_response.json()["access_token"]


def get_event_id(client):
    response = client.get("/api/events")

    assert response.status_code == 200

    events = response.json()
    assert len(events) > 0

    return events[0]["id"]


def test_register_for_event(client):
    token = create_test_user(client)
    event_id = get_event_id(client)

    response = client.post(
        f"/api/events/{event_id}/register",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    data = response.json()

    print("REGISTRATION RESPONSE:", data)

    assert "status" in data



def test_get_my_registrations(client):
    token = create_test_user(client)
    event_id = get_event_id(client)

    register_response = client.post(
        f"/api/events/{event_id}/register",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert register_response.status_code == 200

    response = client.get(
        "/api/registrations/me",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200

    registrations = response.json()

    assert isinstance(registrations, list)
    assert any(
        registration["event_id"] == event_id
        for registration in registrations
    )


def test_cancel_registration(client):
    token = create_test_user(client)
    event_id = get_event_id(client)

    register_response = client.post(
        f"/api/events/{event_id}/register",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert register_response.status_code == 200

    response = client.delete(
        f"/api/events/{event_id}/register",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200