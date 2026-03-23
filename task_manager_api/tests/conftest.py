import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Use the test database
test_engine = create_engine(settings.TEST_DATABASE_URL, pool_pre_ping=True)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session")
def db_tables():
    """Create all tables once per test session, drop them at the end."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session(db_tables):
    """Provide a transactional scope for each test, rolling back after the test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db_session):
    """TestClient with get_db overridden to use the per-test session."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def test_user(client):
    """Register a test user and return the response data."""
    response = client.post(
        "/auth/register",
        json={"email": "testuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture()
def auth_headers(client, test_user):
    """Return Authorization headers for the test user."""
    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def other_user_headers(client):
    """Register a second user and return their auth headers."""
    client.post(
        "/auth/register",
        json={"email": "otheruser@example.com", "password": "otherpassword123"},
    )
    response = client.post(
        "/auth/login",
        json={"email": "otheruser@example.com", "password": "otherpassword123"},
    )
    assert response.status_code == 200
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def sample_project(client, auth_headers):
    """Create a sample project for the test user."""
    response = client.post(
        "/projects",
        json={"name": "Sample Project", "description": "A test project", "status": "active"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()["data"]


@pytest.fixture()
def sample_task(client, auth_headers, sample_project):
    """Create a sample task in the sample project."""
    response = client.post(
        f"/projects/{sample_project['id']}/tasks",
        json={
            "title": "Sample Task",
            "description": "A test task",
            "status": "todo",
            "priority": "medium",
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    return response.json()["data"]
