"""Trust Engine services for V3.

Each factor function takes a ``Profile`` (or ``User``) object and returns a
``TrustFactorBreakdown``.  The overall score is the weighted sum of all
factors, clamped to 0-100, and mapped to a risk level.

Factor weights (must sum to 1.0):
    1. profile_completeness      - 0.40
    2. information_consistency   - 0.25
    3. account_signals           - 0.20
    4. verification_signals      - 0.15
"""

import json
from datetime import datetime, timezone
from typing import List

from app.models.profile import Profile
from app.models.user import User
from app.schemas.trust_score import TrustFactorBreakdown


# ---------------------------------------------------------------------------
# Factor 1 - Profile Completeness (40 %)
# ---------------------------------------------------------------------------
def profile_completeness(profile: Profile) -> TrustFactorBreakdown:
    """Score based on how many required profile sections are filled."""
    weights = {
        "name": 25,
        "age": 15,
        "bio": 20,
        "location": 15,
        "profile_picture": 15,
        "interests": 10,
    }
    score = 0
    missing: List[str] = []
    for field, weight in weights.items():
        val = getattr(profile, field, None)
        if val:
            if field == "interests":
                if len(val) > 0:
                    score += weight
                else:
                    missing.append(field)
            elif isinstance(val, str) and val.strip():
                score += weight
            else:
                score += weight  # non-string truthy values
        else:
            missing.append(field)
    detail = f"Missing fields: {', '.join(missing)}" if missing else "All sections filled"
    return TrustFactorBreakdown(
        name="Profile Completeness",
        weight=0.40,
        score=score,
        contribution=int(round(score * 0.40)),
        details=detail,
    )


# ---------------------------------------------------------------------------
# Factor 2 - Information Consistency (25 %)
# ---------------------------------------------------------------------------
def information_consistency(profile: Profile) -> TrustFactorBreakdown:
    """Score based on whether profile data is internally consistent."""
    score = 100
    issues: List[str] = []

    # Bio length check - too short (< 20 chars) or suspiciously empty
    if profile.bio:
        if len(profile.bio) < 20:
            score -= 30
            issues.append("bio too short")
        elif len(profile.bio) > 500:
            score -= 15
            issues.append("bio unusually long")
    else:
        score -= 25
        issues.append("no bio")

    # Name length / placeholder check
    if profile.name:
        if len(profile.name) < 2:
            score -= 20
            issues.append("name too short")
    else:
        score -= 30
        issues.append("no name")

    # Age sanity
    if profile.age is not None:
        if profile.age < 13 or profile.age > 120:
            score -= 25
            issues.append("age out of expected range")
    else:
        score -= 10
        issues.append("age not provided")

    # Interest count check
    interest_count = len(profile.interests) if profile.interests else 0
    if interest_count == 0:
        score -= 15
        issues.append("no interests listed")
    elif interest_count > 15:
        score -= 10
        issues.append("unusually many interests (may be auto-filled)")

    detail = "All information looks consistent" if not issues else f"Issues: {', '.join(issues)}"
    return TrustFactorBreakdown(
        name="Information Consistency",
        weight=0.25,
        score=max(score, 0),
        contribution=int(round(max(score, 0) * 0.25)),
        details=detail,
    )


# ---------------------------------------------------------------------------
# Factor 3 - Account Signals (20 %)
# ---------------------------------------------------------------------------
def account_signals(user: User) -> TrustFactorBreakdown:
    """Score based on account creation age."""
    now = datetime.now(timezone.utc)
    if user.created_at:
        created = user.created_at
        # SQLite may return naive datetimes; normalize to aware
        if created.tzinfo is None:
            created = created.replace(tzinfo=timezone.utc)
        account_age_days = (now - created).days
    else:
        account_age_days = 0

    # Age-based scoring (0-100)
    if account_age_days >= 365:
        age_score = 100
    elif account_age_days >= 180:
        age_score = 80
    elif account_age_days >= 30:
        age_score = 50
    elif account_age_days >= 7:
        age_score = 25
    else:
        age_score = 5  # brand-new / suspicious

    detail = f"Account is {account_age_days} days old"
    return TrustFactorBreakdown(
        name="Account Signals",
        weight=0.20,
        score=age_score,
        contribution=int(round(age_score * 0.20)),
        details=detail,
    )


# ---------------------------------------------------------------------------
# Factor 4 - Verification / Social Signals (15 %)
# ---------------------------------------------------------------------------
def verification_signals(profile: Profile) -> TrustFactorBreakdown:
    """Score based on profile picture, location, and interest diversity."""
    score = 0
    signals: List[str] = []

    if profile.profile_picture:
        score += 50
        signals.append("has profile picture")
    else:
        signals.append("no profile picture")

    if profile.location:
        score += 25
        signals.append("location provided")
    else:
        signals.append("no location")

    interest_count = len(profile.interests) if profile.interests else 0
    if interest_count >= 3:
        score += 25
        signals.append(f"{interest_count} interests")
    elif interest_count > 0:
        score += 15
        signals.append(f"{interest_count} interests")
    else:
        signals.append("no interests")

    detail = "; ".join(signals)
    return TrustFactorBreakdown(
        name="Verification & Social Signals",
        weight=0.15,
        score=score,
        contribution=int(round(score * 0.15)),
        details=detail,
    )


# ---------------------------------------------------------------------------
# Engine - compute the overall trust score
# ---------------------------------------------------------------------------
FACTOR_FUNCS = [profile_completeness, information_consistency, account_signals, verification_signals]

RISK_THRESHOLDS = {
    "low": 80,
    "moderate": 50,
    # below 50 -> higher
}


def calculate_trust_score(user: User, profile: Profile) -> dict:
    """Compute the full trust assessment for a *user* + *profile* pair.

    Returns a dict with ``score``, ``risk_level``, ``explanation``,
    ``factor_data`` (JSON), and ``factors`` (list of dicts).
    """
    factors: List[TrustFactorBreakdown] = []
    for func in FACTOR_FUNCS:
        if func is account_signals:
            factors.append(func(user))
        else:
            factors.append(func(profile))

    total = sum(f.contribution for f in factors)
    total = min(total, 100)

    if total >= RISK_THRESHOLDS["low"]:
        risk_level = "low"
    elif total >= RISK_THRESHOLDS["moderate"]:
        risk_level = "moderate"
    else:
        risk_level = "higher"

    # Human-readable explanation
    factor_summary = ", ".join(f"{f.name}: {f.score}/100" for f in factors)
    explanation = (
        f"Trust score is {total} ({risk_level} risk). "
        f"Contributing factors: {factor_summary}."
    )

    factor_data = json.dumps([f.model_dump() for f in factors])

    return {
        "score": total,
        "risk_level": risk_level,
        "explanation": explanation,
        "factor_data": factor_data,
        "factors": [f.model_dump() for f in factors],
    }
