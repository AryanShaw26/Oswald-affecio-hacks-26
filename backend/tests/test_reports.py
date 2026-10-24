"""V6 -- Report / User tests.

Covers:
  - POST   /reports             (create report, get confirmation alert)
  - GET    /reports/user/{id}   (list reports against a user)
  - GET    /reports/mine        (list reports filed by the user)
  - Unauthenticated / unauthorized access
  - Invalid report types and self-report prevention
"""

import pytest
from fastapi import status

from app.models.reports import Report
from app.models.alerts import Alert
from app.models.blocks import Block


# === Helpers ===

def _register_user(client, email="reportuser@example.com"):
    """Register a user and return the bearer token."""
    resp = client.post("/auth/register", json={
        "name": "ReportUser",
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


# === Report creation tests ===

class TestReportCreate:
    """Tests for POST /reports."""

    def test_create_report_success(self, client, create_test_database):
        """POST /reports -- authenticated user can report another user."""
        token_a = _register_user(client, email="reporter_a@example.com")
        token_b = _register_user(client, email="reported_b@example.com")
        reported_id = _get_user_id(client, token_b)

        resp = client.post(
            "/reports",
            json={
                "reported_user_id": reported_id,
                "report_type": "scam",
                "description": "This user is asking for money.",
            },
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["report_type"] == "scam"
        assert data["status"] == "pending"

    def test_create_report_invalid_type(self, client, create_test_database):
        """POST /reports -- invalid report_type returns 400."""
        token_a = _register_user(client, email="reporter_c@example.com")
        token_b = _register_user(client, email="reported_d@example.com")
        reported_id = _get_user_id(client, token_b)

        resp = client.post(
            "/reports",
            json={
                "reported_user_id": reported_id,
                "report_type": "invalid_type",
                "description": "Test.",
            },
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_report_self_report_rejected(self, client, create_test_database):
        """POST /reports -- cannot report yourself."""
        token = _register_user(client, email="self_report@example.com")
        user_id = _get_user_id(client, token)

        resp = client.post(
            "/reports",
            json={
                "reported_user_id": user_id,
                "report_type": "spam",
                "description": "Self report.",
            },
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "self" in resp.json()["detail"].lower()

    def test_create_report_unauthenticated(self, client, create_test_database):
        """POST /reports -- unauthenticated request is rejected."""
        resp = client.post(
            "/reports",
            json={
                "reported_user_id": 1,
                "report_type": "spam",
                "description": "Test.",
            },
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_report_creates_alert(self, client, create_test_database, db):
        """POST /reports -- creating a report creates a confirmation alert."""
        token_a = _register_user(client, email="alert_reporter@example.com")
        token_b = _register_user(client, email="alert_target@example.com")
        reported_id = _get_user_id(client, token_b)

        resp = client.post(
            "/reports",
            json={
                "reported_user_id": reported_id,
                "report_type": "harassment",
                "description": "Harassment test.",
            },
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_201_CREATED

        # Verify an alert was created for the reporter
        alerts = db.query(Alert).filter(Alert.user_id == _get_user_id(client, token_a)).all()
        assert len(alerts) >= 1
        assert any(a.alert_type == "report_created" for a in alerts)


# === Report listing tests ===

class TestReportListing:
    """Tests for GET /reports/user/{user_id} and GET /reports/mine."""

    def test_list_user_reports(self, client, create_test_database):
        """GET /reports/user/{id} -- target user can see their reports."""
        token_a = _register_user(client, email="lister_a@example.com")
        token_b = _register_user(client, email="lister_b@example.com")
        reported_id = _get_user_id(client, token_b)

        client.post(
            "/reports",
            json={
                "reported_user_id": reported_id,
                "report_type": "spam",
                "description": "First report.",
            },
            headers=_auth_headers(token_a),
        )

        resp = client.get(
            f"/reports/user/{reported_id}",
            headers=_auth_headers(token_b),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["report_type"] == "spam"

    def test_list_user_reports_forbidden_for_others(self, client, create_test_database):
        """GET /reports/user/{id} -- cannot view another user's reports."""
        token_a = _register_user(client, email="forbid_a@example.com")
        token_b = _register_user(client, email="forbid_b@example.com")
        reported_id = _get_user_id(client, token_b)

        resp = client.get(
            f"/reports/user/{reported_id}",
            headers=_auth_headers(token_a),
        )
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_list_user_reports_unauthenticated(self, client, create_test_database):
        """GET /reports/user/{id} -- unauthenticated access rejected."""
        resp = client.get("/reports/user/1")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_my_reports(self, client, create_test_database):
        """GET /reports/mine -- reporter can see reports they filed."""
        token_a = _register_user(client, email="mine_a@example.com")
        token_b = _register_user(client, email="mine_b@example.com")
        reported_id = _get_user_id(client, token_b)

        client.post(
            "/reports",
            json={
                "reported_user_id": reported_id,
                "report_type": "fake_profile",
                "description": "Fake profile report.",
            },
            headers=_auth_headers(token_a),
        )

        resp = client.get("/reports/mine", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["report_type"] == "fake_profile"
