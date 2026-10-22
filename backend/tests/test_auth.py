import pytest
from fastapi import status
from app.models.user import User
from sqlalchemy.orm import Session


def test_register_success(client, db, create_test_database):
    payload = {"name": "Alice", "email": "alice@example.com", "password": "Secret123!"}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "access_token" in data

    # Verify password is hashed in DB
    # Use the provided db fixture to verify persistence
    user = db.query(User).filter(User.email == payload["email"]).first()
    assert user is not None
    assert user.hashed_password != payload["password"]
    assert user.name == payload["name"]


def test_register_duplicate_email(client, create_test_database):
    payload = {"name": "Bob", "email": "bob@example.com", "password": "Pass123"}
    # first registration
    client.post("/auth/register", json=payload)
    # duplicate
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_login_success(client, create_test_database):
    reg = {"name": "Carol", "email": "carol@example.com", "password": "MyPass!"}
    client.post("/auth/register", json=reg)
    login = {"email": reg["email"], "password": reg["password"]}
    resp = client.post("/auth/login", json=login)
    assert resp.status_code == status.HTTP_200_OK
    token = resp.json()["access_token"]
    assert token

    # Use token to access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/auth/users/me", headers=headers)
    assert me_resp.status_code == status.HTTP_200_OK
    assert me_resp.json()["email"] == reg["email"]


def test_login_invalid_credentials(client, create_test_database):
    # No user exists
    resp = client.post("/auth/login", json={"email": "nosuch@example.com", "password": "nopass"})
    assert resp.status_code == 401
    # Wrong password
    reg = {"name": "Dave", "email": "dave@example.com", "password": "RightPass"}
    client.post("/auth/register", json=reg)
    resp = client.post("/auth/login", json={"email": reg["email"], "password": "WrongPass"})
    assert resp.status_code == 401


def test_protected_without_token(client, create_test_database):
    resp = client.get("/auth/users/me")
    assert resp.status_code in (401, 403)


def test_invalid_token(client, create_test_database):
    headers = {"Authorization": "Bearer invalidtoken"}
    resp = client.get("/auth/users/me", headers=headers)
    assert resp.status_code in (401, 403)
