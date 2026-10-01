from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_agent_chat():
    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Call Agent API with authentication
    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What events are available?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data
def test_agent_event_search():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "Find AI events"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data 
def test_agent_policy_question():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What is the cancellation policy?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "response" in data
    assert "intent" in data
    assert "tools_used" in data   
def test_agent_rag_policy_integration():
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Admin User",
            "email": "admin@events.com",
            "password": "admin123",
            "role": "ADMIN"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": "What is the cancellation policy?"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "RAG_POLICY_SEARCH"
    assert "search_event_policy" in data["tools_used"]
    assert "Cancellation Policy" in data["response"]
def test_agent_register_participant():
    import uuid

    # Create user
    email = f"agent_register_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Agent Register User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Agent Register User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Get an available event
    events_response = client.get("/api/events")

    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0

    event_id = events[0]["id"]

    # Ask Agent to register
    response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Register me for event {event_id}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["intent"] == "REGISTER_PARTICIPANT"
    assert "register_participant" in data["tools_used"]
    assert "Successfully registered" in data["response"]


def test_agent_cancel_registration():
    import uuid

    # Create user
    email = f"agent_cancel_{uuid.uuid4().hex[:8]}@example.com"

    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Agent Cancel User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Login
    login_response = client.post(
        "/api/auth/login",
        json={
            "name": "Agent Cancel User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    # Get an available event
    events_response = client.get("/api/events")

    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0

    event_id = events[0]["id"]

    # Register first
    register_chat = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Register me for event {event_id}"
        }
    )

    assert register_chat.status_code == 200

    # Ask Agent to cancel
    cancel_response = client.post(
        "/api/chat",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "message": f"Cancel my registration for event {event_id}"
        }
    )

    assert cancel_response.status_code == 200

    data = cancel_response.json()

    assert data["intent"] == "CANCEL_REGISTRATION"
    assert "cancel_registration" in data["tools_used"]
    assert "cancelled successfully" in data["response"]            