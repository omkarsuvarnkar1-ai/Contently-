from backend.app.core.config import settings


def test_health_check(client):
    """Test health and readiness endpoint."""
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["service"] == "contently-ai-backend"


def test_demo_user_login(client):
    """Test login with default pre-seeded demo credentials."""
    resp = client.post(
        "/api/auth/login",
        json={"email": settings.DEMO_USER_EMAIL, "password": settings.DEMO_USER_PASSWORD},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["email"] == settings.DEMO_USER_EMAIL
    assert data["user"]["role"] == "Pro Creator"


def test_login_invalid_password(client):
    """Test login rejection when password does not match."""
    resp = client.post(
        "/api/auth/login",
        json={"email": settings.DEMO_USER_EMAIL, "password": "WrongPassword123!"},
    )
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_login_nonexistent_user(client):
    """Test login rejection for unknown email."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "nobody@nowhere.com", "password": "Password123!"},
    )
    assert resp.status_code == 401


def test_signup_success(client):
    """Test new user signup matching the frontend form schema."""
    resp = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Sarah Connor",
            "workEmail": "sarah@cyberdyne.org",
            "password": "Password123!",
        },
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert "token" in data
    assert data["user"]["email"] == "sarah@cyberdyne.org"
    assert data["user"]["name"] == "Sarah Connor"


def test_signup_duplicate_email(client):
    """Test signup rejection for duplicate email."""
    resp = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Omkar Duplicate",
            "workEmail": settings.DEMO_USER_EMAIL,
            "password": "Password123!",
        },
    )
    assert resp.status_code == 400
    assert "already exists" in resp.json()["detail"].lower()


def test_current_user_me_authenticated(client, demo_auth_headers):
    """Test /api/auth/me returns profile for authenticated user."""
    resp = client.get("/api/auth/me", headers=demo_auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == settings.DEMO_USER_EMAIL


def test_current_user_me_unauthenticated(client):
    """Test /api/auth/me rejects unauthenticated requests with 401."""
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_logout(client):
    """Test logout endpoint."""
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
    assert resp.json()["success"] is True
