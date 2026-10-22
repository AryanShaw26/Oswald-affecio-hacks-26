"""Tests for the V3 Trust Engine (trust score calculation + API)."""

import pytest
from fastapi import status

from app.models.user import User
from app.models.profile import Profile, Interest
from app.models.trust_score import TrustScore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_or_create_interest(db, name: str) -> Interest:
    """Return an existing Interest by name or create a new one.

    The ``interests`` table has a UNIQUE constraint on name, so tests sharing
    an in-memory DB must reuse rows instead of inserting duplicates.
    """
    existing = db.query(Interest).filter(Interest.name == name).first()
    if existing:
        return existing
    obj = Interest(name=name)
    db.add(obj)
    db.commit()
    return obj


def _register_and_create_profile(client, db, suffix=""):
    """Register a user, log in, and create a profile. Returns (token, profile_id)."""
    email = f"trustuser{suffix}@example.com"
    reg = {"name": "TestUser", "email": email, "password": "Password123!"}
    resp = client.post("/auth/register", json=reg)
    assert resp.status_code == status.HTTP_201_CREATED
    token = resp.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    profile_payload = {
        "name": "TestUser",
        "age": 28,
        "bio": "I am a test user with a reasonably detailed bio for testing purposes.",
        "location": "San Francisco, CA",
        "profile_picture": "https://example.com/pic.jpg",
        "interests": ["hiking", "reading", "cooking"],
    }
    resp = client.post("/profiles", json=profile_payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    profile_id = resp.json()["id"]

    return token, profile_id


# ---------------------------------------------------------------------------
# Trust factor service tests
# ---------------------------------------------------------------------------
class TestTrustFactors:
    """Unit tests for individual factor functions in app.services.trust_score."""

    def test_profile_completeness_full(self, db):
        from app.services.trust_score import profile_completeness

        user = User(name="FullUser", email="full@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="FullUser",
            age=28,
            bio="This is a full profile with bio, location, picture and interests.",
            location="San Francisco",
            profile_picture="https://example.com/pic.jpg",
        )
        db.add(profile)
        db.commit()

        # Add interests (reuse existing to avoid unique-constraint violations)
        ints = [_get_or_create_interest(db, n) for n in ("hiking", "reading", "cooking")]
        db.add_all(ints)
        db.commit()
        profile.interests = ints
        db.commit()

        factor = profile_completeness(profile)
        assert factor.name == "Profile Completeness"
        assert factor.weight == 0.40
        assert factor.score == 100  # all fields filled
        assert factor.contribution == 40  # 100 * 0.40

    def test_profile_completeness_partial(self, db):
        from app.services.trust_score import profile_completeness

        user = User(name="Partial", email="partial@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="Partial",
            age=None,
            bio=None,
            location=None,
            profile_picture=None,
            interests=[],
        )
        db.add(profile)
        db.commit()

        factor = profile_completeness(profile)
        assert factor.score == 25  # only name present
        assert factor.contribution == int(round(25 * 0.40))

    def test_information_consistency_perfect(self, db):
        from app.services.trust_score import information_consistency

        user = User(name="Consistent", email="consistent@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="Consistent",
            age=30,
            bio="This is a well-written bio that is neither too short nor too long, providing adequate detail for assessment.",
            location="New York",
            profile_picture="https://example.com/img.jpg",
        )
        db.add(profile)
        db.commit()

        ints = [_get_or_create_interest(db, n) for n in ("reading", "cooking", "coding")]
        db.add_all(ints)
        db.commit()
        profile.interests = ints
        db.commit()

        factor = information_consistency(profile)
        assert factor.name == "Information Consistency"
        assert factor.score == 100  # no issues
        assert "All information looks consistent" in factor.details

    def test_information_consistency_issues(self, db):
        from app.services.trust_score import information_consistency

        user = User(name="X", email="short.bio@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="X",  # too short
            age=10,    # below 13
            bio="short",  # too short
            location=None,
        )
        db.add(profile)
        db.commit()

        factor = information_consistency(profile)
        assert factor.score < 100
        assert "bio too short" in factor.details
        assert "age out of expected range" in factor.details

    def test_account_signals_old_account(self, db):
        from app.services.trust_score import account_signals
        from datetime import datetime, timedelta, timezone

        user = User(
            name="OldUser",
            email="olduser@example.com",
            hashed_password="hashed",
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        db.add(user)
        db.commit()

        factor = account_signals(user)
        assert factor.name == "Account Signals"
        assert factor.score == 100  # >= 365 days
        assert factor.weight == 0.20

    def test_account_signals_new_account(self, db):
        from app.services.trust_score import account_signals

        user = User(
            name="NewUser",
            email="newuser@example.com",
            hashed_password="hashed",
        )
        db.add(user)
        db.commit()

        factor = account_signals(user)
        assert factor.score == 5  # brand new

    def test_verification_signals_with_picture_and_location(self, db):
        from app.services.trust_score import verification_signals
        from app.models.profile import Interest

        user = User(name="Verified", email="verified@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        ints = [Interest(name=n) for n in ("music", "sports", "travel")]
        db.add_all(ints)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="Verified",
            profile_picture="https://example.com/pic.jpg",
            location="London",
            interests=ints,
        )
        db.add(profile)
        db.commit()

        factor = verification_signals(profile)
        assert factor.score == 100  # 50 + 25 + 25
        assert "has profile picture" in factor.details
        assert "location provided" in factor.details

    def test_verification_signals_empty(self, db):
        from app.services.trust_score import verification_signals

        user = User(name="NoPic", email="nopic@example.com", hashed_password="hashed")
        db.add(user)
        db.commit()

        profile = Profile(user_id=user.id, name="NoPic")
        db.add(profile)
        db.commit()

        factor = verification_signals(profile)
        assert factor.score == 0
        assert "no profile picture" in factor.details


# ---------------------------------------------------------------------------
# Full trust score calculation test
# ---------------------------------------------------------------------------
class TestCalculateTrustScore:
    def test_high_score_profile(self, db):
        from app.services.trust_score import calculate_trust_score
        from datetime import datetime, timedelta, timezone

        user = User(
            name="Trusted",
            email="trusted@example.com",
            hashed_password="hashed",
            created_at=datetime.now(timezone.utc) - timedelta(days=400),
        )
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="Trusted",
            age=30,
            bio="This is a well-written bio with adequate detail for testing purposes.",
            location="San Francisco",
            profile_picture="https://example.com/pic.jpg",
            interests=[],
        )
        db.add(profile)
        db.commit()

        result = calculate_trust_score(user, profile)
        assert result["score"] >= 80
        assert result["risk_level"] == "low"
        assert "score" in result["explanation"]
        assert "factors" in result
        assert len(result["factors"]) == 4

    def test_low_score_profile(self, db):
        from app.services.trust_score import calculate_trust_score

        user = User(
            name="X",
            email="lowscore@example.com",
            hashed_password="hashed",
        )
        db.add(user)
        db.commit()

        profile = Profile(
            user_id=user.id,
            name="X",
            age=10,
            bio="hi",
        )
        db.add(profile)
        db.commit()

        result = calculate_trust_score(user, profile)
        assert result["score"] < 50
        assert result["risk_level"] == "higher"


# ---------------------------------------------------------------------------
# Trust API route tests
# ---------------------------------------------------------------------------
class TestTrustRoutes:
    def test_analyze_and_get_score(self, client, create_test_database):
        """Full flow: register, create profile, analyze, retrieve."""
        token, profile_id = _register_and_create_profile(client, None, suffix="_analyze")

        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post(f"/trust/analyze/{profile_id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["score"] is not None
        assert 0 <= data["score"] <= 100
        assert data["risk_level"] in ("low", "moderate", "higher")
        assert "explanation" in data
        assert "factors" in data

        resp = client.get(f"/trust/profile/{profile_id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["score"] is not None
        assert "factor_data" in data

    def test_get_trust_score_without_token(self, client, create_test_database):
        resp = client.get("/trust/profile/1")
        assert resp.status_code in (401, 403)

    def test_analyze_nonexistent_profile(self, client, create_test_database):
        token, _ = _register_and_create_profile(client, None, suffix="_nonexist")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/trust/analyze/99999", headers=headers)
        assert resp.status_code == 404

    def test_me_trust_score(self, client, create_test_database):
        token, _ = _register_and_create_profile(client, None, suffix="_me")
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.get("/trust/me", headers=headers)
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert 0 <= data["score"] <= 100
        assert "risk_level" in data
        assert "factor_data" in data

    def test_trust_score_persisted(self, client, db, create_test_database):
        token, profile_id = _register_and_create_profile(client, None, suffix="_persist")
        headers = {"Authorization": f"Bearer {token}"}

        resp = client.post(f"/trust/analyze/{profile_id}", headers=headers)
        assert resp.status_code == status.HTTP_200_OK

        trust = db.query(TrustScore).filter(TrustScore.profile_id == profile_id).first()
        assert trust is not None
        assert trust.risk_level in ("low", "moderate", "higher")
