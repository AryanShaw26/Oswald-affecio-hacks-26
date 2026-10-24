"""V6 -- Dashboard tests.

Covers GET /dashboard -- aggregated safety dashboard for the authenticated user.
"""

import pytest
from fastapi import status

from app.models.reports import Report
from app.models.blocks import Block
from app.models.alerts import Alert
from app.models.trust_score import TrustScore


# === Helpers ===

def _register_user(client, email="dashboard@example.com"):
    resp = client.post("/auth/register", json={
        "name": "DashUser",
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


def _create_profile(client, token):
    """Create a basic profile for the current user and return the profile id."""
    resp = client.post(
        "/profiles",
        json={
            "name": "DashUser",
            "age": 30,
            "bio": "A test user for dashboard testing.",
            "location": "San Francisco, CA",
            "profile_picture": "https://example.com/pic.jpg",
            "interests": ["hiking", "reading"],
        },
        headers=_auth_headers(token),
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["id"]


# === Dashboard tests ===

class TestDashboard:
    """Tests for GET /dashboard."""

    def test_dashboard_empty(self, client, create_test_database):
        """GET /dashboard -- returns default values when no data exists."""
        token = _register_user(client, email="dash_empty@example.com")
        # No profile created — should still return 200 with nulls / zeros
        resp = client.get("/dashboard", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["user_id"] == _get_user_id(client, token)
        assert data["trust_score"] is None
        assert data["blocks_given_count"] == 0
        assert data["blocks_received_count"] == 0
        assert data["reports_count"] == 0
        assert data["alerts_count"] == 0
        assert data["unread_alerts_count"] == 0

    def test_dashboard_with_trust_score(self, client, create_test_database):
        """GET /dashboard -- includes the latest trust score after analysis."""
        token = _register_user(client, email="dash_trust@example.com")
        _create_profile(client, token)

        # Trigger trust analysis (auto-persists)
        resp = client.get("/trust/me", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK

        resp = client.get("/dashboard", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["trust_score"] is not None
        assert "score" in data["trust_score"]
        assert "risk_level" in data["trust_score"]

    def test_dashboard_with_alerts(self, client, create_test_database, db):
        """GET /dashboard -- includes recent alerts."""
        token = _register_user(client, email="dash_alerts@example.com")
        user_id = _get_user_id(client, token)

        # Simulate a report from another user to trigger an alert
        token_b = _register_user(client, email="dash_alerts_b@example.com")
        reported_id = _get_user_id(client, token_b)
        client.post(
            "/reports",
            json={"reported_user_id": reported_id, "report_type": "spam",
                  "description": "Test report for dashboard."},
            headers=_auth_headers(token),
        )

        resp = client.get("/dashboard", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["recent_alerts"] is not None
        assert data["alerts_count"] >= 1
        assert data["unread_alerts_count"] >= 1

    def test_dashboard_with_blocks(self, client, create_test_database, db):
        """GET /dashboard -- includes block counts."""
        token_a = _register_user(client, email="dash_blocks_a@example.com")
        token_b = _register_user(client, email="dash_blocks_b@example.com")
        blocked_id = _get_user_id(client, token_b)

        client.post(
            "/blocks",
            json={"blocked_user_id": blocked_id, "reason": "Test block"},
            headers=_auth_headers(token_a),
        )

        resp = client.get("/dashboard", headers=_auth_headers(token_a))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["blocks_given_count"] == 1
        assert data["blocks_received_count"] == 0

    def test_dashboard_with_reports(self, client, create_test_database, db):
        """GET /dashboard -- includes report count."""
        token_a = _register_user(client, email="dash_reports_a@example.com")
        token_b = _register_user(client, email="dash_reports_b@example.com")
        reported_id = _get_user_id(client, token_b)

        # Report B by A
        client.post(
            "/reports",
            json={"reported_user_id": reported_id, "report_type": "scam",
                  "description": "Dashboard report test."},
            headers=_auth_headers(token_a),
        )

        # B views dashboard — should see report about them
        resp = client.get("/dashboard", headers=_auth_headers(token_b))
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["reports_count"] >= 1
        assert len(data["recent_reports"]) >= 1

    def test_dashboard_unauthenticated(self, client, create_test_database):
        """GET /dashboard -- unauthenticated access rejected."""
        resp = client.get("/dashboard")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED
