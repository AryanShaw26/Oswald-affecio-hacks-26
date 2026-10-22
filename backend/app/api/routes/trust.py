"""Trust Engine routes for V3.

- GET  /trust/profile/{profile_id}   Retrieve the latest trust score for a profile
- POST /trust/analyze/{profile_id}   Calculate (and persist) a fresh trust score
- GET  /trust/me                    Shortcut to the calling user's profile trust score
"""

import json

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.profile import Profile
from app.models.trust_score import TrustScore
from app.schemas.trust_score import TrustScoreRead, TrustScoreResponse
from app.services.trust_score import calculate_trust_score

router = APIRouter(prefix="/trust", tags=["trust"])


@router.get("/profile/{profile_id}", response_model=TrustScoreRead)
def get_profile_trust_score(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the latest trust score for *profile_id*.

    Any authenticated user may view a profile's trust score — it is
    public assessment data.
    """
    trust = db.query(TrustScore).filter(TrustScore.profile_id == profile_id).order_by(TrustScore.created_at.desc()).first()
    if not trust:
        raise HTTPException(status_code=404, detail="No trust score found for this profile. Run POST /trust/analyze/{profile_id} first.")
    return trust


@router.post("/analyze/{profile_id}", response_model=TrustScoreResponse)
def analyze_profile(
    profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Calculate and persist a fresh trust score for *profile_id*.

    Only the profile owner or the user themselves can trigger a recalculation,
    but since trust is a public metric any authenticated user can trigger it.
    """
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    user = db.query(User).filter(User.id == profile.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    assessment = calculate_trust_score(user, profile)

    trust = TrustScore(
        user_id=profile.user_id,
        profile_id=profile_id,
        score=assessment["score"],
        risk_level=assessment["risk_level"],
        explanation=assessment["explanation"],
        factor_data=assessment["factor_data"],
    )
    db.add(trust)
    db.commit()
    db.refresh(trust)

    # Return the enriched response (includes parsed ``factors`` list)
    return TrustScoreResponse(
        score=trust.score,
        risk_level=trust.risk_level,
        explanation=trust.explanation,
        factors=json.loads(assessment["factor_data"]),
    )


@router.get("/me", response_model=TrustScoreRead)
def get_my_trust_score(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Shortcut: retrieve the trust score for the calling user's own profile."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found — create a profile first")

    trust = db.query(TrustScore).filter(TrustScore.profile_id == profile.id).order_by(TrustScore.created_at.desc()).first()
    if not trust:
        # Auto-calculate if no existing score
        assessment = calculate_trust_score(current_user, profile)
        trust = TrustScore(
            user_id=profile.user_id,
            profile_id=profile.id,
            score=assessment["score"],
            risk_level=assessment["risk_level"],
            explanation=assessment["explanation"],
            factor_data=assessment["factor_data"],
        )
        db.add(trust)
        db.commit()
        db.refresh(trust)

    return trust
