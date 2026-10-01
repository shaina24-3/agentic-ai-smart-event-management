from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)


def test_register_user():
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"

    response = client.post(
        "/api/auth/register",
        json={
            "name": "Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["email"] == email
    assert data["name"] == "Test User"


def test_login_user():
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"

    # Register user
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Login Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Login user
    response = client.post(
        "/api/auth/login",
        json={
            "name": "Login Test User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password():
    email = f"wrongpass_{uuid.uuid4().hex[:8]}@example.com"

    # Register user first
    register_response = client.post(
        "/api/auth/register",
        json={
            "name": "Wrong Password User",
            "email": email,
            "password": "test123",
            "role": "USER"
        }
    )

    assert register_response.status_code == 200

    # Try incorrect password
    response = client.post(
        "/api/auth/login",
        json={
            "name": "Wrong Password User",
            "email": email,
            "password": "wrongpassword",
            "role": "USER"
        }
    )

    assert response.status_code == 401