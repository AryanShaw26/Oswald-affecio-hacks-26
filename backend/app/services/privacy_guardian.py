"""V5 — Privacy Guardian detection engine.

Uses deterministic regex and rule-based patterns to detect common types of
sensitive information in user messages *before* they are sent.

Detection categories (per implementation guide):
* phone_number    — international / US-style phone numbers
* email           — standard email addresses
* address         — street-address-like patterns
* upi_id          — Indian UPI identifiers (e.g. abc@upi)
* bank_details    — IBAN, routing+account, card numbers
* password        — common password-variable patterns
* government_id   — SSN, Aadhaar, PAN, passport-like patterns
* financial_info  — credit-card-like numbers, account references

The engine returns a PrivacyResult with a clear warning and recommendation.
"""

from __future__ import annotations

import re
from typing import List, Tuple

from app.schemas.privacy_alert import PrivacyResult

# ── Compiled regex patterns ────────────────────────────────────────────
# Phone: captures +1-555-123-4567, (555) 123-4567, 555.123.4567, 5551234567
_PHONE_RE = re.compile(
    r"""
    (?<!\d)                   # not preceded by another digit
    (?:\+?1[\s.-]?)?          # optional country code
    (?:\(?\d{3}\)?[\s.-]?)    # area code
    \d{3}[\s.-]?\d{4}         # subscriber number
    (?!\d)                    # not followed by another digit
    """,
    re.VERBOSE,
)

# Email
_EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)

# Physical address — simple heuristic: number + street + city/state/zip
_ADDRESS_RE = re.compile(
    r"\b\d+\s+[A-Za-z0-9\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|"
    r"Lane|Ln|Drive|Dr|Court|Ct|Place|Pl|Square|Sq|Circle|Cir|Terrace|Ter)\b.*"
    r"(?:[A-Za-z\s]+),\s*(?:[A-Z]{2})\s*\d{5}\b",
    re.IGNORECASE,
)

# UPI ID — name@upi or name@bankname (India)
_UPI_RE = re.compile(
    r"\b[A-Za-z0-9._-]+@[A-Za-z]{2,}\b"
)

# Bank details — IBAN, card numbers (16 digits grouped), routing+account
_BANK_RE = re.compile(
    r"""
    (?:
        # IBAN — 2 letters + 2 digits + 2 digits + 4 chars + 2 letters + 3 digits + 4 chars
        \b[A-Z]{2}\d{2}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\s?\d{2}\b
        |
        # 16-digit card number, optionally grouped by spaces/dashes
        \b(?:\d{4}[\s-]?){3}\d{4}\b
        |
        # US routing + account (xxx-xxxx-xxxx-xxxx)
        \b\d{3}-?\d{3}-?\d{4}-?\d{3,10}\b
    )
    """,
    re.VERBOSE,
)

# Password patterns — common variable names + typical password assignments
_PASSWORD_RE = re.compile(
    r"(?:password|passwd|pwd)\s*[:=]\s*\S+",
    re.IGNORECASE,
)


# Government ID patterns — SSN, Indian Aadhaar, PAN, passport
_GOV_ID_RE = re.compile(
    r"""
    (?:
        # SSN: xxx-xx-xxxx
        \b\d{3}-\d{2}-\d{4}\b
        |
        # Indian Aadhaar: 12 digits (grouped 4-4-4)
        \b\d{4}\s\d{4}\s\d{4}\b
        |
        # Indian PAN: 5 letters + 4 digits + 1 letter
        \b[A-Z]{5}\d{4}[A-Z]\b
        |
        # Passport: 1 letter + 7-8 digits
        \b[A-PR-WYa-pr-wy]\d{7,8}\b
    )
    """,
    re.VERBOSE,
)

# Financial information — credit-card-like, account number references
_FINANCIAL_RE = re.compile(
    r"""
    (?:
        # Credit card reference
        \b(?:\d{4}[\s-]?){3}\d{4}\b
        |
        # Account number keyword + digits
        \baccount\s*(?:\#|no\.?|number)?\s*\d{6,18}\b
        |
        \brouting\s*(?:\#|no\.?|number)?\s*\d{6,12}\b
        |
        \bifsc\s*[:=]?\s*[A-Z]{4}0[A-Z0-9]{6}\b
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)

# Minimum address length to reduce false positives
_MIN_ADDRESS_LEN = 10

# ── Type descriptions for human-readable warnings ──────────────────────
TYPE_DESCRIPTIONS = {
    "phone_number": "phone number",
    "email": "email address",
    "address": "physical address",
    "upi_id": "UPI identifier",
    "bank_details": "bank or account details",
    "password": "password-like information",
    "government_id": "government ID number",
    "financial_info": "financial information",
}


def _check_phone(text: str) -> bool:
    matches = _PHONE_RE.findall(text)
    # Filter out matches that are part of longer digit sequences (dates, etc.)
    matched = [m for m in matches if sum(c.isdigit() for c in m) >= 10]
    return len(matched) > 0


def _check_email(text: str) -> bool:
    return bool(_EMAIL_RE.search(text))


def _check_address(text: str) -> bool:
    if len(text) < _MIN_ADDRESS_LEN:
        return False
    return bool(_ADDRESS_RE.search(text))


def _check_upi(text: str) -> bool:
    """UPI IDs look like name@upi or name@bankname."""
    for m in _UPI_RE.finditer(text):
        local, domain = m.group().rsplit("@", 1)
        # Skip if it looks like an email (domain has a dot)
        if "." in domain:
            continue
        if len(domain) <= 8 and not domain.isdigit():
            return True
    return False


def _check_bank(text: str) -> bool:
    return bool(_BANK_RE.search(text))


def _check_password(text: str) -> bool:
    return bool(_PASSWORD_RE.search(text))


def _check_gov_id(text: str) -> bool:
    return bool(_GOV_ID_RE.search(text))


def _check_financial(text: str) -> bool:
    return bool(_FINANCIAL_RE.search(text))


def _truncate_excerpt(text: str, limit: int = 200) -> str:
    """Truncate *text* to *limit* characters for storage.

    Used by the route layer to store a minimal excerpt that does NOT
    contain the full sensitive value (V5-15 — sensitive-value minimization).
    """
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[:limit] + "…"


# ── Public API ────────────────────────────────────────────────────────
def detect_sensitive_info(message: str) -> PrivacyResult:
    """Scan *message* for sensitive information and return a PrivacyResult.

    The function is deterministic (no external API calls) and never
    raises — it always returns a valid PrivacyResult.
    """
    if not message or not message.strip():
        return PrivacyResult(
            flagged=False,
            risk_level="low",
            detected_types=[],
            warning="No content to analyze.",
            recommendation="",
        )

    detected_types: List[str] = []

    if _check_phone(message):
        detected_types.append("phone_number")
    if _check_email(message):
        detected_types.append("email")
    if _check_address(message):
        detected_types.append("address")
    if _check_upi(message):
        detected_types.append("upi_id")
    if _check_bank(message):
        detected_types.append("bank_details")
    if _check_password(message):
        detected_types.append("password")
    if _check_gov_id(message):
        detected_types.append("government_id")
    if _check_financial(message):
        detected_types.append("financial_info")

    flagged = len(detected_types) > 0

    if not flagged:
        return PrivacyResult(
            flagged=False,
            risk_level="low",
            detected_types=[],
            warning="No sensitive information detected in this message.",
            recommendation="You're good to go — no sensitive data was found.",
        )

    # Build human-readable description of detected types (without exposing values)
    type_names = [TYPE_DESCRIPTIONS[t] for t in detected_types if t in TYPE_DESCRIPTIONS]
    if len(type_names) <= 2:
        types_str = " and ".join(type_names)
    else:
        types_str = ", ".join(type_names[:-1]) + f", and {type_names[-1]}"

    warning = (
        f"This message contains information that could identify or "
        f"financially expose you ({types_str}). "
        f"Please review before sharing."
    )
    recommendation = "Remove the sensitive information before sending."

    # Any sensitive type is high risk
    risk_level = "high" if any(
        t in {"phone_number", "email", "address", "upi_id", "bank_details",
              "password", "government_id", "financial_info"}
        for t in detected_types
    ) else "medium"

    return PrivacyResult(
        flagged=True,
        risk_level=risk_level,
        detected_types=detected_types,
        warning=warning,
        recommendation=recommendation,
    )

