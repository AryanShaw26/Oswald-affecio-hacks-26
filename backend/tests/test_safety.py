"""V4 -- Conversation Safety API & service tests.

Covers checklist items V4-01 through V4-18 plus API-level acceptance criteria.
"""

import json
import logging
from unittest.mock import patch, MagicMock

import pytest
from fastapi import status

from app.models.conversation_safety import ConversationSafety


# === Helpers ===

def _register_user(client, email="safety@example.com"):
    """Register a user and return the bearer token."""
    resp = client.post("/auth/register", json={
        "name": "SafetyTester",
        "email": email,
        "password": "Pass123!",
    })
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["access_token"]


def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def _make_rate_limit_error():
    from openai import RateLimitError
    return RateLimitError("Rate limited", response=MagicMock(), body=None)


def _make_api_error():
    from openai import APIError
    return APIError("Server error", MagicMock(), body=None)


def _mock_openai_success(categories=None, risk_level="low", flagged=False,
                         summary="Test summary", recommendation="Test recommendation"):
    """Return a mock OpenAI client whose .chat.completions.create() yields JSON."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = json.dumps({
        "risk_level": risk_level,
        "categories": categories or [],
        "flagged": flagged,
        "summary": summary,
        "recommendation": recommendation,
    })
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


def _mock_openai_invalid_json():
    """OpenAI returns non-JSON text."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "I am not valid JSON"
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client

# === V4-01: API connection test ===

class TestSafetyConnection:
    """V4-01 -- Verify that an analysis request reaches the AI service."""

    def test_request_reaches_openai(self, monkeypatch):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(risk_level="low", flagged=False, categories=[])
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Hello, how are you today?")
        assert mock_client.chat.completions.create.called
        call_kwargs = mock_client.chat.completions.create.call_args
        assert "messages" in call_kwargs.kwargs
        messages = call_kwargs.kwargs["messages"]
        assert any(m["role"] == "system" for m in messages)
        assert any(m["role"] == "user" and "Hello" in m["content"] for m in messages)
        assert result["risk_level"] == "low"
        assert result["flagged"] is False

    def test_api_key_not_in_response(self, monkeypatch):
        """V4-02 -- Ensure no API key leaks into the response dict."""
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(risk_level="low", flagged=False, categories=[])
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)
        with patch.object(cs.settings, "OPENAI_API_KEY", "sk-test-secret-12345"):
            result = cs.analyze_message("test message", user_id=1)
        result_str = str(result)
        assert "sk-" not in result_str
        assert "OPENAI_API_KEY" not in result_str


# === V4-03 through V4-10: Category detection ===

class TestSafetyCategories:
    """V4-03 through V4-10 -- Verify the service detects each risk category."""

    @pytest.mark.parametrize(
        "message_text, mock_cats, mock_risk, mock_flagged",
        [
            ("Hi there! How's your day going?", [], "low", False),
            (
                "Your account will be suspended unless you click this link "
                "and verify your password right now.",
                ["scam"], "high", True,
            ),
            ("Can you send me $2000 to my bank account?",
             ["financial_request"], "high", True),
            ("You are a worthless idiot and everyone hates you",
             ["harassment"], "medium", True),
            ("I'm going to find you and break your legs",
             ["threat"], "high", True),
            ("If you don't help me I'll hurt myself and it'll be your fault",
             ["manipulation"], "medium", True),
            ("Can you give me your phone number and address?",
             ["suspicious_request"], "medium", True),
            ("Please share your password and SSN",
             ["sensitive_information_request"], "high", True),
        ],
    )
    def test_category_detection(self, monkeypatch, message_text,
                                mock_cats, mock_risk, mock_flagged):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(
            categories=mock_cats, risk_level=mock_risk, flagged=mock_flagged,
        )
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message(message_text)
        assert result["categories"] == mock_cats
        assert result["risk_level"] == mock_risk
        assert result["flagged"] == mock_flagged

    def test_empty_message(self):
        from app.services import conversation_safety as cs
        result = cs.analyze_message("")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False


# === V4-11: Malformed responses ===

class TestSafetyMalformedResponses:
    """V4-11 -- Handle malformed or unparseable OpenAI responses gracefully."""

    def test_invalid_json_response(self, monkeypatch):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_invalid_json()
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Test message")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False

    def test_empty_response(self, monkeypatch):
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Test message")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False

    def test_missing_required_keys(self, monkeypatch):
        """Response missing required keys is handled gracefully."""
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = \
            json.dumps({"risk_level": "high"})
        mock_client.chat.completions.create.return_value = mock_response
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Test message")
        assert result["flagged"] is False


# === V4-12: API failures ===

class TestSafetyApiFailures:
    """V4-12 -- API errors are caught and translated to safe defaults."""

    def test_api_error_handled(self, monkeypatch):
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = _make_api_error()
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Hello")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False

    def test_generic_exception_handled(self, monkeypatch):
        """Unexpected exceptions never propagate -- safe fallback returned."""
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = \
            RuntimeError("Unexpected")
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Hello")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False


# === V4-13: Rate limits ===

class TestSafetyRateLimits:
    """V4-13 -- RateLimitError returns a safe fallback."""

    def test_rate_limit_handled(self, monkeypatch):
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = \
            _make_rate_limit_error()
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Hello")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False
        assert "rate" in result["summary"].lower()


# === V4-14: Timeout ===

class TestSafetyTimeout:
    """V4-14 -- Timeout errors return a safe fallback."""

    def test_timeout_handled(self, monkeypatch):
        from app.services import conversation_safety as cs
        from openai import Timeout

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = \
            Timeout("Timed out")
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        result = cs.analyze_message("Hello")
        assert result["risk_level"] == "low"
        assert result["flagged"] is False


# === V4-15: Authentication ===

class TestSafetyAuth:
    """V4-15 -- Protected safety endpoint rejects unauthenticated access."""

    def test_analyze_without_token(self, client, create_test_database):
        resp = client.post("/safety/analyze", json={"message": "test"})
        assert resp.status_code in (401, 403)

    def test_invalid_token_rejected(self, client, create_test_database):
        headers = {"Authorization": "Bearer invalid.token.here"}
        resp = client.post("/safety/analyze", json={"message": "test"},
                           headers=headers)
        assert resp.status_code in (401, 403)


# === V4-16: User isolation ===

class TestSafetyUserIsolation:
    """V4-16 -- User cannot retrieve another user's private analysis."""

    def test_cannot_access_other_user_analysis(self, client, create_test_database):
        token_a = _register_user(client, email="userA@example.com")
        token_b = _register_user(client, email="userB@example.com")

        from app.services import conversation_safety as cs
        mock_client = _mock_openai_success(
            risk_level="high", flagged=True, categories=["scam"],
        )
        with patch.object(cs, "_create_client", lambda: mock_client):
            resp = client.post(
                "/safety/analyze",
                json={"message": "Scam attempt! Send money now"},
                headers=_auth_headers(token_a),
            )
        assert resp.status_code == status.HTTP_200_OK

        from app.core.database import SessionLocal
        db_session = SessionLocal()
        try:
            analysis = db_session.query(ConversationSafety).filter(
                ConversationSafety.user_id == 1
            ).first()
            assert analysis is not None
            analysis_id = analysis.id
        finally:
            db_session.close()

        resp_b = client.get(
            f"/safety/conversations/{analysis_id}",
            headers=_auth_headers(token_b),
        )
        assert resp_b.status_code == status.HTTP_404_NOT_FOUND


# === V4-17: Persistence ===

class TestSafetyPersistence:
    """V4-17 -- Analysis is stored and retrievable."""

    def test_analysis_persisted(self, client, db, create_test_database):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(
            risk_level="high", flagged=True, categories=["financial_request"],
        )
        with patch.object(cs, "_create_client", lambda: mock_client):
            token = _register_user(client, email="persist@example.com")
            resp = client.post(
                "/safety/analyze",
                json={"message": "Send me money please"},
                headers=_auth_headers(token),
            )
        assert resp.status_code == status.HTTP_200_OK

        analysis = db.query(ConversationSafety).first()
        assert analysis is not None
        assert analysis.risk_level in ("low", "medium", "high")

    def test_analysis_retrievable(self, client, create_test_database):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(
            risk_level="high", flagged=True, categories=["scam"],
        )
        with patch.object(cs, "_create_client", lambda: mock_client):
            token = _register_user(client, email="retrieve@example.com")
            resp = client.post(
                "/safety/analyze",
                json={"message": "This is a normal conversation"},
                headers=_auth_headers(token),
            )
        assert resp.status_code == status.HTTP_200_OK

        from app.core.database import SessionLocal
        db_session = SessionLocal()
        try:
            analysis = db_session.query(ConversationSafety).first()
            assert analysis is not None
            analysis_id = analysis.id
        finally:
            db_session.close()

        resp = client.get(
            f"/safety/conversations/{analysis_id}",
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "risk_level" in data
        assert "categories" in data
        assert "flagged" in data
        assert "summary" in data
        assert "recommendation" in data


# === V4-18: Sensitive logging prevention ===

class TestSafetyLogging:
    """V4-18 -- The raw message content is never logged."""

    def test_message_not_logged(self, monkeypatch, caplog):
        from app.services import conversation_safety as cs

        mock_client = _mock_openai_success(
            risk_level="low", flagged=False, categories=[],
        )
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        secret_phrase = "SUPER_SECRET_PHRASE_12345"
        with caplog.at_level(logging.DEBUG,
                             logger="app.services.conversation_safety"):
            cs.analyze_message(secret_phrase, user_id=42)

        for record in caplog.records:
            assert secret_phrase not in record.getMessage()

    def test_error_logs_do_not_leak_message(self, monkeypatch, caplog):
        from app.services import conversation_safety as cs

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = \
            RuntimeError("fail")
        monkeypatch.setattr(cs, "_create_client", lambda: mock_client)

        secret_phrase = "TOP_SECRET_VALUE_999"
        with caplog.at_level(logging.DEBUG,
                             logger="app.services.conversation_safety"):
            cs.analyze_message(secret_phrase, user_id=42)

        for record in caplog.records:
            assert secret_phrase not in record.getMessage()

    def test_get_nonexistent_analysis(self, client, create_test_database):
        """GET /safety/conversations/{id} -- 404 for missing ID."""
        token = _register_user(client, email="nonexist@example.com")
        resp = client.get(
            "/safety/conversations/99999",
            headers=_auth_headers(token),
        )
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_get_analysis(self, client, create_test_database):
        """GET /safety/conversations/{id} -- rejected without token."""
        resp = client.get("/safety/conversations/1")
        assert resp.status_code in (401, 403)


