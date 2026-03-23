import pytest


def test_register_success(client):
    response = client.post(
        "/auth/register",
        json={"email": "newuser@example.com", "password": "mypassword123"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["message"] == "User registered successfully"
    assert body["data"]["email"] == "newuser@example.com"
    assert "id" in body["data"]
    assert "created_at" in body["data"]
    # Ensure password is not leaked
    assert "password" not in body["data"]
    assert "hashed_password" not in body["data"]


def test_register_duplicate_email(client, test_user):
    response = client.post(
        "/auth/register",
        json={"email": "testuser@example.com", "password": "anotherpassword123"},
    )
    assert response.status_code == 422


def test_register_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={"email": "not-an-email", "password": "mypassword123"},
    )
    assert response.status_code == 422


def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={"email": "valid@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_success(client, test_user):
    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Login successful"
    assert "access_token" in body["data"]
    assert body["data"]["token_type"] == "bearer"


def test_login_wrong_password(client, test_user):
    response = client.post(
        "/auth/login",
        json={"email": "testuser@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "somepassword"},
    )
    assert response.status_code == 401


def test_access_protected_endpoint_without_token(client):
    response = client.get("/projects")
    assert response.status_code == 403


def test_access_protected_endpoint_with_bad_token(client):
    response = client.get(
        "/projects",
        headers={"Authorization": "Bearer this.is.invalid"},
    )
    assert response.status_code == 401
