from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_invalid_event():
    response = client.post(
        "/api/events/999999/register"
    )

    assert response.status_code in [401, 400]

def test_create_event_without_login():
    response = client.post(
        "/api/events",
        json={
            "title": "Unauthorized Event",
            "description": "This should fail",
            "date": "2026-12-25",
            "time": "10:00 AM",
            "venue_id": 1,
            "capacity": 50
        }
    )

    assert response.status_code == 401 

def test_duplicate_registration():
    import uuid

    # Create a new user
    email = f"duplicate_{uuid.uuid4().hex[:8]}@example.com"

    register = client.post(
        "/api/auth/register",
        json={
            "name": "Duplicate Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register.status_code == 200

    # Login
    login = client.post(
        "/api/auth/login",
        json={
            "name": "Duplicate Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login.status_code == 200
    token = login.json()["access_token"]

    # Get an existing event
    events = client.get("/api/events")
    assert events.status_code == 200
    event_id = events.json()[0]["id"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # First registration
    first = client.post(
        f"/api/events/{event_id}/register",
        headers=headers
    )

    assert first.status_code == 200

    # Second registration
    second = client.post(
        f"/api/events/{event_id}/register",
        headers=headers
    )

    assert second.status_code == 400
def test_normal_user_cannot_create_event():
    import uuid

    email = f"user_admin_test_{uuid.uuid4().hex[:8]}@example.com"

    register = client.post(
        "/api/auth/register",
        json={
            "name": "Normal User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register.status_code == 200

    login = client.post(
        "/api/auth/login",
        json={
            "name": "Normal User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    response = client.post(
        "/api/events",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "title": "Unauthorized Event",
            "description": "User should not create this",
            "date": "2026-12-31",
            "time": "10:00 AM",
            "venue_id": 1,
            "capacity": 50
        }
    )

    assert response.status_code == 403   
def test_unauthenticated_user_cannot_update_event():
    response = client.put(
        "/api/events/1",
        json={
            "title": "Unauthorized Update"
        }
    )

    assert response.status_code == 401


def test_unauthenticated_user_cannot_cancel_event():
    response = client.delete(
        "/api/events/1"
    )

    assert response.status_code == 401     