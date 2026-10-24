"""V6 -- Safety Alerts tests.

Covers:
  - GET    /alerts               (list all alerts for current user)
  - GET    /alerts/unread        (list only unread alerts)
  - GET    /alerts/unread-count  (count unread alerts)
  - POST   /alerts/read          (mark all as read)
  - GET    /alerts/{id}           (get single alert)
  - Unauthenticated / unauthorized access
"""

import pytest
from fastapi import status

from app.models.alerts import Alert
from app.services.alerts import create_alert


# === Helpers ===

def _register_user(client, email="alertuser@example.com"):
    """Register a user and return the bearer token."""
    resp = client.post("/auth/register", json={
        "name": "AlertUser",
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


# === Alert listing tests ===

class TestAlertListing:
    """Tests for GET /alerts and GET /alerts/unread."""

    def test_list_alerts_unauthenticated(self, client, create_test_database):
        """GET /alerts -- unauthenticated access rejected."""
        resp = client.get("/alerts")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_alerts_empty(self, client, create_test_database):
        """GET /alerts -- empty list when no alerts exist."""
        token = _register_user(client, email="alerts_empty@example.com")
        resp = client.get("/alerts", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json() == []

    def test_list_alerts_with_data(self, client, create_test_database, db):
        """GET /alerts -- returns alerts sorted by most recent first."""
        token = _register_user(client, email="alerts_data@example.com")
        user_id = _get_user_id(client, token)

        # Create alerts via service directly
        create_alert(
            db=db,
            user_id=user_id,
            alert_type="system_notification",
            severity="low",
            message="First alert",
        )
        create_alert(
            db=db,
            user_id=user_id,
            alert_type="report_created",
            severity="medium",
            message="Second alert",
        )

        resp = client.get("/alerts", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        # Most recent first
        assert data[0]["message"] == "Second alert"

    def test_list_unread_alerts(self, client, create_test_database, db):
        """GET /alerts/unread -- returns only unread alerts."""
        token = _register_user(client, email="alerts_unread@example.com")
        user_id = _get_user_id(client, token)

        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="low", message="Unread 1")
        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="low", message="Unread 2")

        # Mark one as read via the API
        client.post("/alerts/read", headers=_auth_headers(token))
        # Create another unread one
        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="low", message="Still unread")

        resp = client.get("/alerts/unread", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data) == 1
        assert data[0]["message"] == "Still unread"


# === Alert read / count tests ===

class TestAlertReadOperations:
    """Tests for mark-read and unread-count endpoints."""

    def test_unread_count(self, client, create_test_database, db):
        """GET /alerts/unread-count -- returns correct count."""
        token = _register_user(client, email="count_test@example.com")
        user_id = _get_user_id(client, token)

        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="low", message="Alert 1")
        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="medium", message="Alert 2")

        resp = client.get("/alerts/unread-count", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["unread_count"] == 2

    def test_mark_all_read(self, client, create_test_database, db):
        """POST /alerts/read -- marks all alerts as read."""
        token = _register_user(client, email="read_all@example.com")
        user_id = _get_user_id(client, token)

        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="low", message="Alert to read")
        create_alert(db=db, user_id=user_id, alert_type="system_notification",
                     severity="medium", message="Another to read")

        resp = client.post("/alerts/read", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["message"]  # non-empty message

        # Verify all are now read
        resp = client.get("/alerts/unread-count", headers=_auth_headers(token))
        assert resp.json()["unread_count"] == 0

    def test_mark_all_read_unauthenticated(self, client, create_test_database):
        """POST /alerts/read -- unauthenticated access rejected."""
        resp = client.post("/alerts/read")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


# === Single alert tests ===

class TestAlertSingle:
    """Tests for GET /alerts/{id}."""

    def test_get_single_alert(self, client, create_test_database, db):
        """GET /alerts/{id} -- returns a single alert."""
        token = _register_user(client, email="single_alert@example.com")
        user_id = _get_user_id(client, token)

        alert = create_alert(
            db=db,
            user_id=user_id,
            alert_type="system_notification",
            severity="low",
            message="Single alert detail",
        )

        resp = client.get(f"/alerts/{alert.id}", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["alert_type"] == "system_notification"
        assert data["message"] == "Single alert detail"
        assert data["is_read"] is False

    def test_get_nonexistent_alert(self, client, create_test_database):
        """GET /alerts/{id} -- 404 for missing alert."""
        token = _register_user(client, email="missing_alert@example.com")
        resp = client.get("/alerts/99999", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_404_NOT_FOUND
