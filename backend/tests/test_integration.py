import uuid
from fastapi.testclient import TestClient
from app.main import app


def test_complete_user_event_workflow():

    with TestClient(app) as client:

        # 1. Register a new user
        email = f"integration_{uuid.uuid4().hex[:8]}@example.com"

        register_response = client.post(
            "/api/auth/register",
            json={
                "name": "Integration Test User",
                "email": email,
                "password": "test123",
                "role": "USER"
            }
        )

        assert register_response.status_code == 200

        # 2. Login
        login_response = client.post(
            "/api/auth/login",
            json={
                "name": "Integration Test User",
                "email": email,
                "password": "test123",
                "role": "USER"
            }
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        headers = {
            "Authorization": f"Bearer {token}"
        }

        # 3. Get available events
        events_response = client.get("/api/events")

        assert events_response.status_code == 200

        events = events_response.json()

        assert len(events) > 0

        event_id = events[0]["id"]

        # 4. Register for the event
        registration_response = client.post(
            f"/api/events/{event_id}/register",
            headers=headers
        )

        assert registration_response.status_code == 200

        # 5. Check user's registrations
        registrations_response = client.get(
            "/api/registrations/me",
            headers=headers
        )

        assert registrations_response.status_code == 200

        registrations = registrations_response.json()

        assert any(
            registration["event_id"] == event_id
            for registration in registrations
        )

        # 6. Cancel registration
        cancel_response = client.delete(
            f"/api/events/{event_id}/register",
            headers=headers
        )

        assert cancel_response.status_code == 200