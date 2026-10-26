import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from backend.app.core.config import settings
from backend.app.core.database import Base, get_db
from backend.app.main import app
from backend.app.services.seed_service import SeedService

# Isolated Test Database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def db_session():
    connection = engine_test.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    # Seed demo user
    SeedService.seed_initial_data(session)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def demo_auth_headers(client):
    """Obtain valid auth header for demo user."""
    resp = client.post(
        "/api/auth/login",
        json={"email": settings.DEMO_USER_EMAIL, "password": settings.DEMO_USER_PASSWORD},
    )
    assert resp.status_code == 200
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def second_user_auth_headers(client):
    """Register and obtain auth header for a second distinct user."""
    resp = client.post(
        "/api/auth/signup",
        json={
            "fullName": "Alice Smith",
            "workEmail": "alice@innovate.co",
            "password": "SecurePassword123!",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["token"]
    return {"Authorization": f"Bearer {token}"}
