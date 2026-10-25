from fastapi import status


def _register(client, email, name):
    response = client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": "Pass123!"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()["access_token"]


def _create_profile(client, token, name, location):
    response = client.post(
        "/profiles",
        json={
            "name": name,
            "age": 28,
            "bio": "A valid bio for the profile security audit.",
            "location": location,
            "profile_picture": "https://example.com/avatar.png",
            "interests": ["travel", "music", "reading"],
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()


def test_profile_access_requires_ownership(client, create_test_database):
    token_a = _register(client, "a.security@example.com", "Alice")
    token_b = _register(client, "b.security@example.com", "Bob")

    profile_a = _create_profile(client, token_a, "Alice", "New York")
    profile_b = _create_profile(client, token_b, "Bob", "Boston")

    own_response = client.get(
        f"/profiles/{profile_a['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert own_response.status_code == status.HTTP_200_OK
    assert own_response.json()["user_id"] == profile_a["user_id"]

    unauthorized_response = client.get(
        f"/profiles/{profile_b['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert unauthorized_response.status_code == status.HTTP_403_FORBIDDEN
    assert unauthorized_response.json()["detail"] == "Not authorized to access this profile"

    unauthorized_response_b = client.get(
        f"/profiles/{profile_a['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert unauthorized_response_b.status_code == status.HTTP_403_FORBIDDEN
    assert unauthorized_response_b.json()["detail"] == "Not authorized to access this profile"
