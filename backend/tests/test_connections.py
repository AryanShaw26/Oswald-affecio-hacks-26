from fastapi import status


def _register(client, email, name="User"):
    response = client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "Pass123!"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["access_token"]


def _profile(client, token, name):
    response = client.post(
        "/profiles",
        json={
            "name": name,
            "age": 28,
            "bio": "This is a short but valid bio for a profile.",
            "location": "Test City",
            "profile_picture": "https://example.com/avatar.png",
            "interests": ["travel", "music", "reading"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def test_discovery_lists_other_profiles(client, create_test_database):
    token_a = _register(client, "a.discovery@example.com", "Alice")
    token_b = _register(client, "b.discovery@example.com", "Bob")
    _profile(client, token_a, "Alice")
    _profile(client, token_b, "Bob")

    response = client.get("/profiles/discover", headers={"Authorization": f"Bearer {token_a}"})
    assert response.status_code == status.HTTP_200_OK
    payload = response.json()
    assert any(item["name"] == "Bob" for item in payload)
    assert all(item["name"] != "Alice" for item in payload)


def test_connection_request_persists(client, create_test_database):
    token_a = _register(client, "a.connection@example.com", "Alice")
    token_b = _register(client, "b.connection@example.com", "Bob")
    _profile(client, token_a, "Alice")
    _profile(client, token_b, "Bob")

    response = client.post(
        "/connections",
        json={"target_user_id": 2},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["status"] == "pending"

    status_response = client.get(
        "/connections/status/2",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert status_response.status_code == status.HTTP_200_OK
    assert status_response.json()["status"] == "pending"
