"""V6 -- Block / User tests.

Covers:
  - POST   /blocks                (block a user, get confirmation alert)
  - GET    /blocks                (list blocked users)
  - DELETE /blocks/{target_id}    (unblock a user)
  - GET    /blocks/check/{id}     (check if user is blocked)
  - GET    /blocks/ids            (list blocked user IDs)
  - Unauthenticated / unauthorized access
  - Duplicate block prevention
"""

import pytest
from fastapi import status

from app.models.blocks import Block
from app.models.alerts import Alert


# === Helpers ===

def _register_user(client, email="blockuser@example.com"):
    """Register a user and return the bearer token."""
    resp = client.post("/auth/register", json={
        "name": "BlockUser",
        "email": email,
        "password": "Pass123!",
    })
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _get_user_id(client, token):
    resp = client.get("/auth/users/me", headers=_auth_headers(token))
    return resp.json()["id"]


# === Block creation tests ===

class TestBlockCreate:
    """Tests for POST /blocks."""

    def test_block_user_success(self, client, create_test_database):
        """POST /blocks -- authenticated user can block another user."""
        token_a = _register_user(client, email="blocker_a@example.com")
        token_b = _register_user(client, email="blocked_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        resp = client.post(
            "/blocks",
            json={"blocked_user_id": blocked_id, "reason": "Inappropriate messages."},
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "message" in data
        assert data["id"] > 0

    def test_block_self_rejected(self, client, create_test_database):
        """POST /blocks -- cannot block yourself."""
        token = _register_user(client, email="self_block@example.com")
        user_id = _get_user_id(client, token)

        resp = client.post(
            "/blocks",
            json={"blocked_user_id": user_id, "reason": "test"},
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "self" in resp.json()["detail"].lower()

    def test_duplicate_block_rejected(self, client, create_test_database):
        """POST /blocks -- cannot block the same user twice."""
        token_a = _register_user(client, email="dup_a@example.com")
        token_b = _register_user(client, email="dup_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        # First block succeeds
        resp1 = client.post(
            "/blocks",
            json={"blocked_user_id": blocked_id},
            headers=_auth_headers(token_a),
        )
        assert resp1.status_code == status.HTTP_201_CREATED

        # Second block fails
        resp2 = client.post(
            "/blocks",
            json={"blocked_user_id": blocked_id},
            headers=_auth_headers(token_a),
        )
        assert resp2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already" in resp2.json()["detail"].lower()

    def test_block_unauthenticated(self, client, create_test_database):
        """POST /blocks -- unauthenticated request is rejected."""
        resp = client.post("/blocks", json={"blocked_user_id": 1})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_block_creates_alert(self, client, create_test_database, db):
        """POST /blocks -- creating a block creates a confirmation alert."""
        token_a = _register_user(client, email="alert_blocker@example.com")
        token_b = _register_user(client, email="alert_blocked@example.com")
        blocked_id = _get_user_id(client, token_b)

        resp = client.post(
            "/blocks",
            json={"blocked_user_id": blocked_id},
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_201_CREATED

        alerts = db.query(Alert).filter(Alert.user_id == _get_user_id(client, token_a)).all()
        assert len(alerts) >= 1
        assert any(a.alert_type == "block_applied" for a in alerts)


# === Block listing and management tests ===

class TestBlockManagement:
    """Tests for GET /blocks, DELETE /blocks/{id}, GET /blocks/check/{id}."""

    def test_list_blocks(self, client, create_test_database):
        """GET /blocks -- list all users the current user has blocked."""
        token_a = _register_user(client, email="list_a@example.com")
        token_b = _register_user(client, email="list_b@example.com")
        token_c = _register_user(client, email="list_c@example.com")
        blocked_b = _get_user_id(client, token_b)
        blocked_c = _get_user_id(client, token_c)

        client.post("/blocks", json={"blocked_user_id": blocked_b}, headers=_auth_headers(token_a))
        client.post("/blocks", json={"blocked_user_id": blocked_c}, headers=_auth_headers(token_a))

        resp = client.get("/blocks", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2

    def test_list_blocks_empty(self, client, create_test_database):
        """GET /blocks -- empty list when no blocks exist."""
        token = _register_user(client, email="empty_blocks@example.com")
        resp = client.get("/blocks", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_list_blocks_unauthenticated(self, client, create_test_database):
        """GET /blocks -- unauthenticated access rejected."""
        resp = client.get("/blocks")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unblock_user(self, client, create_test_database, db):
        """DELETE /blocks/{target_id} -- unblock a previously blocked user."""
        token_a = _register_user(client, email="unblock_a@example.com")
        token_b = _register_user(client, email="unblock_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        # Block
        client.post("/blocks", json={"blocked_user_id": blocked_id}, headers=_auth_headers(token_a))

        # Unblock
        resp = client.delete(f"/blocks/{blocked_id}", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK

        # Verify it's gone
        assert db.query(Block).filter(
            Block.blocker_id == _get_user_id(client, token_a),
            Block.blocked_id == blocked_id,
        ).first() is None

    def test_unblock_nonexistent(self, client, create_test_database):
        """DELETE /blocks/{id} -- 404 for non-existent block."""
        token = _register_user(client, email="unblock_nonexist@example.com")
        resp = client.delete("/blocks/99999", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_check_block_true(self, client, create_test_database):
        """GET /blocks/check/{id} -- returns is_blocked=True after blocking."""
        token_a = _register_user(client, email="check_a@example.com")
        token_b = _register_user(client, email="check_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        client.post("/blocks", json={"blocked_user_id": blocked_id}, headers=_auth_headers(token_a))

        resp = client.get(f"/blocks/check/{blocked_id}", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_blocked"] is True

    def test_check_block_false(self, client, create_test_database):
        """GET /blocks/check/{id} -- returns is_blocked=False before blocking."""
        token_a = _register_user(client, email="check_false_a@example.com")
        token_b = _register_user(client, email="check_false_b@example.com")
        target_id = _get_user_id(client, token_b)

        resp = client.get(f"/blocks/check/{target_id}", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["is_blocked"] is False

    def test_blocked_ids_endpoint(self, client, create_test_database):
        """GET /blocks/ids -- returns list of blocked user IDs."""
        token_a = _register_user(client, email="ids_a@example.com")
        token_b = _register_user(client, email="ids_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        client.post("/blocks", json={"blocked_user_id": blocked_id}, headers=_auth_headers(token_a))

        resp = client.get("/blocks/ids", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        ids = resp.json()
        assert isinstance(ids, list)
        assert blocked_id in ids

