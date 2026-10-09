from fastapi.testclient import TestClient
from app.main import app
from app.auth import verify_password
from app.database import SessionLocal
from app.main import login
from app.models import AuditLog, User
from app.schemas import UserCreate
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


def test_login_upgrades_matching_legacy_plaintext_password():
    db = SessionLocal()
    email = f"legacy_{uuid.uuid4().hex[:8]}@example.com"
    user = User(
        name="Legacy Login User",
        email=email,
        password_hash="legacy-pass-123",
        role="USER",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        result = login(
            UserCreate(
                name=user.name,
                email=email,
                password="legacy-pass-123",
                role="USER",
            ),
            db,
        )

        db.refresh(user)
        assert result["token_type"] == "bearer"
        assert user.password_hash.startswith(("$2a$", "$2b$", "$2y$"))
        assert verify_password("legacy-pass-123", user.password_hash)
    finally:
        db.query(AuditLog).filter(AuditLog.user_id == user.id).delete(synchronize_session=False)
        db.delete(user)
        db.commit()
        db.close()