"""V5 -- Privacy Guardian detection and API tests.

Covers checklist items V5-01 through V5-15 plus API-level acceptance criteria
for POST /privacy/check and GET /privacy/alerts.

Synthetic test data only — no real sensitive values are used.
"""

import json
from unittest.mock import patch

import pytest
from fastapi import status

from app.models.privacy_alert import PrivacyAlert
from app.schemas.privacy_alert import PrivacyResult
from app.services.privacy_guardian import detect_sensitive_info


# === Helpers ===

def _register_user(client, email="privacy@example.com"):
    """Register a user and return the bearer token."""
    resp = client.post("/auth/register", json={
        "name": "PrivacyTester",
        "email": email,
        "password": "Pass123!",
    })
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _check_privacy(client, token, message):
    """Call POST /privacy/check and return the response."""
    return client.post(
        "/privacy/check",
        json={"message": message},
        headers=_auth_headers(token),
    )


def _get_user_id(client, token):
    """Helper: fetch current user's id from the /auth/users/me endpoint."""
    resp = client.get("/auth/users/me", headers=_auth_headers(token))
    return resp.json()["id"]


# === V5-01 through V5-08: Individual detection tests ===

class TestPrivacyDetection:
    """V5-01 through V5-08 -- Verify the service detects each sensitive type."""

    # -- V5-01: Phone number --
    def test_phone_number_detected(self):
        result = detect_sensitive_info("Contact me at 9876543210.")
        assert result.flagged is True
        assert "phone_number" in result.detected_types

    # -- V5-02: Email address --
    def test_email_detected(self):
        result = detect_sensitive_info("Send the document to testuser@example.com.")
        assert result.flagged is True
        assert "email" in result.detected_types

    # -- V5-03: Physical address --
    def test_physical_address_detected(self):
        result = detect_sensitive_info(
            "I live at 123 Main Street, Springfield, IL 62704."
        )
        assert result.flagged is True
        assert "address" in result.detected_types

    # -- V5-04: UPI ID --
    def test_upi_id_detected(self):
        result = detect_sensitive_info("Pay me at testuser@upi.")
        assert result.flagged is True
        assert "upi_id" in result.detected_types

    # -- V5-05: Bank details --
    def test_bank_details_detected(self):
        result = detect_sensitive_info("My card is 4532 1234 5678 9012")
        assert result.flagged is True
        assert "bank_details" in result.detected_types

    # -- V5-06: Password --
    def test_password_detected(self):
        result = detect_sensitive_info("My password = supersecret123")
        assert result.flagged is True
        assert "password" in result.detected_types

    # -- V5-07: Government ID --
    def test_government_id_detected(self):
        result = detect_sensitive_info("My SSN is 123-45-6789")
        assert result.flagged is True
        assert "government_id" in result.detected_types

    # -- V5-08: Financial information --
    def test_financial_info_detected(self):
        result = detect_sensitive_info("Routing #123456789")
        assert result.flagged is True
        assert "financial_info" in result.detected_types


# === V5-09: Multiple sensitive types ===

class TestMultipleTypes:
    """V5-09 -- Multiple types returned in one result."""

    def test_phone_and_gov_id_detected(self):
        result = detect_sensitive_info(
            "Call me at 9876543210 — my SSN is 123-45-6789."
        )
        assert result.flagged is True
        assert len(result.detected_types) > 1
        assert "phone_number" in result.detected_types
        assert "government_id" in result.detected_types

    def test_phone_and_email_detected(self):
        result = detect_sensitive_info(
            "Call me at 9876543210 or email me at test@example.com."
        )
        assert result.flagged is True
        assert len(result.detected_types) > 1
        assert "phone_number" in result.detected_types
        assert "email" in result.detected_types


# === V5-10 / V5-11: Safe messages ===

class TestSafeMessages:
    """V5-10 and V5-11 -- No unnecessary warnings for harmless text."""

    def test_safe_message_not_flagged(self):
        """V5-10 -- Safe message does not trigger a warning."""
        result = detect_sensitive_info(
            "It was nice talking to you. Have a good day."
        )
        assert result.flagged is False
        assert result.risk_level == "low"

    def test_friendly_conversation_not_flagged(self):
        """V5-11 -- Harmless text does not trigger an unjustified warning."""
        result = detect_sensitive_info(
            "The weather is nice today, and I'm going to the park."
        )
        assert result.flagged is False
        assert result.risk_level == "low"

    def test_empty_message_not_flagged(self):
        """V5-10 -- Empty message handled gracefully, no flag."""
        result = detect_sensitive_info("")
        assert result.flagged is False
        assert result.risk_level == "low"

    def test_whitespace_message_not_flagged(self):
        """V5-11 -- Whitespace-only content does not trigger a warning."""
        result = detect_sensitive_info("   ")
        assert result.flagged is False


# === V5-12: Result structure ===

class TestResultStructure:
    """V5-12 -- Flagged, detected types, warning, recommendation returned."""

    def test_flagged_result_has_all_fields(self):
        result = detect_sensitive_info("My SSN is 123-45-6789.")
        assert isinstance(result, PrivacyResult)
        assert result.flagged is True
        assert result.risk_level in ("low", "medium", "high")
        assert isinstance(result.detected_types, list)
        assert len(result.detected_types) > 0
        assert isinstance(result.warning, str)
        assert len(result.warning) > 0
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0

    def test_warning_mentions_detected_types(self):
        """V5-12 -- Warning text references the detected type descriptions."""
        result = detect_sensitive_info("Contact me at 9876543210.")
        assert "phone number" in result.warning.lower()

    def test_recommendation_provided(self):
        """V5-12 -- A recommendation is provided for flagged messages."""
        result = detect_sensitive_info("My SSN is 123-45-6789.")
        assert len(result.recommendation) > 0

    def test_safe_result_has_all_fields(self):
        """V5-12 -- Safe messages still return a complete PrivacyResult."""
        result = detect_sensitive_info("It was nice talking to you.")
        assert isinstance(result, PrivacyResult)
        assert result.flagged is False
        assert result.risk_level == "low"
        assert isinstance(result.detected_types, list)
        assert isinstance(result.warning, str)
        assert isinstance(result.recommendation, str)


# === V5-13: Persistence (API integration) ===

class TestPersistence:
    """V5-13 -- Privacy alert stored when sensitive info is detected."""

    def test_alert_stored_on_detection(self, client):
        from app.core.database import SessionLocal

        token = _register_user(client, email="persist@example.com")
        resp = _check_privacy(client, token, "My SSN is 123-45-6789")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["flagged"] is True
        assert resp.json()["risk_level"] == "high"

        db = SessionLocal()
        try:
            alert = db.query(PrivacyAlert).filter(
                PrivacyAlert.user_id == _get_user_id(client, token)
            ).first()
            assert alert is not None
            assert alert.flagged is True
            assert "government_id" in alert.detected_types
            assert alert.risk_level == "high"
            assert alert.warning
            assert alert.recommendation
            assert alert.message_excerpt
        finally:
            db.close()

    def test_no_alert_stored_for_safe_message(self, client):
        from app.core.database import SessionLocal

        token = _register_user(client, email="safe@example.com")
        resp = _check_privacy(client, token, "It was nice talking to you.")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["flagged"] is False

        db = SessionLocal()
        try:
            alert = db.query(PrivacyAlert).filter(
                PrivacyAlert.user_id == _get_user_id(client, token)
            ).first()
            assert alert is None
        finally:
            db.close()

    def test_alert_detected_types_stored_as_csv(self, client):
        from app.core.database import SessionLocal

        token = _register_user(client, email="csv@example.com")
        resp = _check_privacy(client, token, "Call me at 9876543210.")
        assert resp.status_code == status.HTTP_200_OK
        assert "phone_number" in resp.json()["detected_types"]

        db = SessionLocal()
        try:
            alert = db.query(PrivacyAlert).filter(
                PrivacyAlert.user_id == _get_user_id(client, token)
            ).first()
            assert alert is not None
            assert "phone_number" in alert.detected_types
        finally:
            db.close()


# === V5-14: User isolation ===

class TestUserIsolation:
    """V5-14 -- User cannot retrieve another user's alerts."""

    def test_other_users_alerts_not_visible(self, client):
        token1 = _register_user(client, email="isolated1@example.com")
        token2 = _register_user(client, email="isolated2@example.com")

        # User 1 creates a flagged alert
        resp1 = _check_privacy(client, token1, "My SSN is 123-45-6789.")
        assert resp1.status_code == status.HTTP_200_OK
        assert resp1.json()["flagged"] is True

        # User 2 has no alerts of their own
        resp2 = client.get("/privacy/alerts", headers=_auth_headers(token2))
        assert resp2.status_code == status.HTTP_200_OK
        alerts_b = resp2.json()
        assert len(alerts_b) == 0

        # User 1 sees their own alert
        resp1b = client.get("/privacy/alerts", headers=_auth_headers(token1))
        assert resp1b.status_code == status.HTTP_200_OK
        alerts_a = resp1b.json()
        assert len(alerts_a) >= 1

    def test_alerts_filtered_by_user(self, client):
        """V5-14 -- Alerts list only includes the authenticated user's alerts."""
        token_a = _register_user(client, email="userA@example.com")
        token_b = _register_user(client, email="userB@example.com")

        # Both users create alerts
        _check_privacy(client, token_a, "My SSN is 123-45-6789.")
        _check_privacy(client, token_b, "Call me at 9876543210.")

        # User A should only see their own alerts
        resp_a = client.get("/privacy/alerts", headers=_auth_headers(token_a))
        alerts_a = resp_a.json()
        user_a_id = _get_user_id(client, token_a)
        for a in alerts_a:
            assert a["user_id"] == user_a_id

        # User B should only see their own alerts
        resp_b = client.get("/privacy/alerts", headers=_auth_headers(token_b))
        alerts_b = resp_b.json()
        user_b_id = _get_user_id(client, token_b)
        for a in alerts_b:
            assert a["user_id"] == user_b_id

        assert len(alerts_a) == 1
        assert len(alerts_b) == 1


# === V5-15: Sensitive-value minimization ===

class TestSensitiveValueMinimization:
    """V5-15 -- Actual sensitive value is not unnecessarily persisted."""

    def test_excerpt_is_truncated_for_long_messages(self, client):
        """V5-15 -- Long messages are truncated in stored excerpt."""
        from app.core.database import SessionLocal

        token = _register_user(client, email="truncate@example.com")
        # Message well over 200 characters
        long_message = "My SSN is 123-45-6789. " * 30
        _check_privacy(client, token, long_message)

        db = SessionLocal()
        try:
            alert = db.query(PrivacyAlert).filter(
                PrivacyAlert.user_id == _get_user_id(client, token)
            ).first()
            assert alert is not None
            # _truncate_excerpt caps at 200 chars + ellipsis
            assert len(alert.message_excerpt) <= 201
        finally:
            db.close()

    def test_excerpt_stored_for_context(self, client):
        """V5-15 -- An excerpt is stored (limited context, not full message)."""
        from app.core.database import SessionLocal

        token = _register_user(client, email="context@example.com")
        message = "My SSN is 123-45-6789, please don't share it."
        _check_privacy(client, token, message)

        db = SessionLocal()
        try:
            alert = db.query(PrivacyAlert).filter(
                PrivacyAlert.user_id == _get_user_id(client, token)
            ).first()
            assert alert is not None
            assert isinstance(alert.message_excerpt, str)
            assert len(alert.message_excerpt) > 0
        finally:
            db.close()


# === API validation tests ===

class TestPrivacyApi:
    """Request-level validation for POST /privacy/check and GET /privacy/alerts."""

    def test_valid_message_returns_privacy_result(self, client):
        token = _register_user(client, email="valid@example.com")
        resp = _check_privacy(client, token, "Contact me at 9876543210.")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "flagged" in data
        assert "risk_level" in data
        assert "detected_types" in data
        assert "warning" in data
        assert "recommendation" in data

    def test_safe_message_returns_not_flagged(self, client):
        token = _register_user(client, email="safe_api@example.com")
        resp = _check_privacy(client, token, "It was nice talking to you.")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["flagged"] is False

    def test_empty_message_returns_422(self, client):
        """POST /privacy/check -- empty/invalid body returns controlled 4xx."""
        token = _register_user(client, email="empty@example.com")
        resp = client.post(
            "/privacy/check",
            json={"message": ""},
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_missing_message_field_returns_422(self, client):
        """POST /privacy/check -- missing message field returns 4xx."""
        token = _register_user(client, email="missing@example.com")
        resp = client.post(
            "/privacy/check",
            json={},
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_unauthenticated_check_rejected(self, client):
        """POST /privacy/check -- unauthenticated request is rejected."""
        resp = client.post(
            "/privacy/check",
            json={"message": "My SSN is 123-45-6789."},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_invalid_token_rejected(self, client):
        """POST /privacy/check -- invalid token is rejected."""
        resp = client.post(
            "/privacy/check",
            json={"message": "My SSN is 123-45-6789."},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_unauthenticated_alerts_rejected(self, client):
        """GET /privacy/alerts -- unauthenticated access is rejected."""
        resp = client.get("/privacy/alerts")
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_authenticated_alerts_returns_list(self, client):
        """GET /privacy/alerts -- authenticated user receives a list."""
        token = _register_user(client, email="list@example.com")
        resp = client.get("/privacy/alerts", headers=_auth_headers(token))
        assert resp.status_code == status.HTTP_200_OK
        assert isinstance(resp.json(), list)
