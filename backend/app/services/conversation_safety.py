"""V4 — AI Conversation Safety Analyzer service.

Dedicated service that sends a message to the OpenAI API, validates the
structured JSON response, and returns a ConversationSafetyResult.

Design notes (per implementation guide):
* OPENAI_API_KEY is loaded from environment variables (backend only).
* A structured system prompt forces the model to return JSON with the
  required fields.
* All OpenAI failures — timeouts, auth errors, rate limits, malformed
  JSON — are caught and translated into a *safe default* result.
* The raw message is never logged.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Optional

from openai import OpenAI, APIError, RateLimitError, AuthenticationError, APITimeoutError

from app.core.config import settings

logger = logging.getLogger(__name__)

# ── Risk categories the detector can return ────────────────────────────
ALL_CATEGORIES = [
    "scam",
    "financial_request",
    "harassment",
    "threat",
    "manipulation",
    "suspicious_request",
    "sensitive_information_request",
]

# ── Structured system prompt ───────────────────────────────────────────
SYSTEM_PROMPT = (
    "You are a conversation safety analyzer.  Your task is to analyze the "
    "user's message and classify potential safety risks.  You MUST respond "
    "with valid JSON only — no prose, no markdown.\n\n"
    "Return a JSON object with exactly these keys:\n"
    '  "risk_level": one of "low", "medium", "high"\n'
    '  "categories": a JSON array of risk categories from this list: '
    + ", ".join(ALL_CATEGORIES) + "\n"
    '  "flagged": boolean — true if any category applies\n'
    '  "summary": a short explanation of what was detected or why the '
    "message is safe\n"
    '  "recommendation": actionable advice for the user\n\n'
    "Classification guidelines:\n"
    "- scam: messages attempting fraud, phishing, or fake account recovery\n"
    "- financial_request: requests for money, payments, or financial credentials\n"
    "- harassment: abusive, insulting, or unwanted repeated contact\n"
    "- threat: threats of violence, harm, or intimidation\n"
    "- manipulation: emotional manipulation, guilt-tripping, love-bombing\n"
    "- suspicious_request: unusual or out-of-context requests for personal info\n"
    "- sensitive_information_request: asking for passwords, IDs, bank details, etc.\n\n"
    "If the message is normal and safe, set risk_level to 'low', categories to "
    "[], flagged to false, and provide a brief safe summary.\n\n"
    "Respond ONLY with the JSON object.\n"
)

# Safe fallback when OpenAI API is unavailable or returns unexpected data.
_FALLBACK_RESULT = {
    "risk_level": "low",
    "categories": [],
    "flagged": False,
    "summary": (
        "Safety analysis is temporarily unavailable. "
        "This message has not been flagged."
    ),
    "recommendation": "Review the message manually before sharing sensitive information.",
}


def _truncate(text: str, limit: int = 500) -> str:
    """Truncate *text* to *limit* characters for storage."""
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


def _parse_openai_response(content: str) -> Optional[dict]:
    """Parse and validate the JSON returned by the model.

    Returns ``None`` if the content is not valid JSON or is missing
    required keys.
    """
    if not content or not content.strip():
        return None
    try:
        data = json.loads(content)
    except (json.JSONDecodeError, ValueError):
        try:
            cleaned = content.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.strip("```")
            data = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError, TypeError):
            return None

    if not isinstance(data, dict):
        return None

    required_keys = {"risk_level", "categories", "flagged", "summary", "recommendation"}
    if not required_keys.issubset(data.keys()):
        return None

    # Normalise / validate types
    if not isinstance(data.get("categories"), list):
        data["categories"] = []
    if not isinstance(data.get("flagged"), bool):
        data["flagged"] = len(data.get("categories", [])) > 0
    data["risk_level"] = str(data.get("risk_level", "low"))
    data["summary"] = str(data.get("summary", ""))
    data["recommendation"] = str(data.get("recommendation", ""))

    return data


def _create_client() -> Optional[OpenAI]:
    """Create an OpenAI client using the backend env var, or ``None``
    if the API key is not configured.
    """
    api_key = settings.OPENAI_API_KEY or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("OPENAI_API_KEY is not set; returning fallback result.")
        return None
    try:
        return OpenAI(api_key=api_key)
    except Exception:  # pragma: no cover — defensive
        logger.exception("Failed to initialise OpenAI client")
        return None


def analyze_message(message: str, user_id: Optional[int] = None) -> dict:
    """Analyze *message* for conversation-safety risks via the OpenAI API.

    Returns a dict with keys: ``risk_level``, ``categories``, ``flagged``,
    ``summary``, ``recommendation``.

    All errors produce a *safe* result — the function never raises.
    """
    if not message or not message.strip():
        result = dict(_FALLBACK_RESULT)
        result["summary"] = "Empty message provided."
        return result

    # Never log the actual message content
    logger.info("Analyzing safety (user_id=%s, length=%d)", user_id, len(message))

    client = _create_client()
    if client is None:
        return dict(_FALLBACK_RESULT)

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            temperature=0.3,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        parsed = _parse_openai_response(content)

        if parsed is None:
            logger.warning(
                "OpenAI returned unparseable response (user_id=%s).", user_id,
            )
            fallback = dict(_FALLBACK_RESULT)
            fallback["summary"] = (
                "The AI analysis service returned an unexpected response. "
                "This message has not been flagged."
            )
            return fallback

        # Validate categories against known list
        valid_categories = [c for c in parsed["categories"] if c in ALL_CATEGORIES]
        parsed["categories"] = valid_categories
        if not valid_categories and parsed["flagged"]:
            parsed["flagged"] = False

        logger.info(
            "Safety analysis complete (user_id=%s, risk=%s, flagged=%s)",
            user_id, parsed["risk_level"], parsed["flagged"],
        )
        return parsed

    except AuthenticationError:
        logger.error("OpenAI authentication error (invalid API key)")
        return dict(_FALLBACK_RESULT)
    except RateLimitError:
        logger.warning("OpenAI rate limit reached; returning fallback result")
        fallback = dict(_FALLBACK_RESULT)
        fallback["summary"] = (
            "The AI service is currently rate-limited. "
            "This message has not been flagged."
        )
        return fallback
    except APITimeoutError:
        logger.warning("OpenAI request timed out; returning fallback result")
        fallback = dict(_FALLBACK_RESULT)
        fallback["summary"] = (
            "The AI service timed out. "
            "This message has not been flagged."
        )
        return fallback
    except APIError as exc:
        logger.warning("OpenAI API error: %s", exc)
        return dict(_FALLBACK_RESULT)
    except Exception:  # pragma: no cover — catch-all safety net
        logger.exception("Unexpected error during safety analysis")
        return dict(_FALLBACK_RESULT)
