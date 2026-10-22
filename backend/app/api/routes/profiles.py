"""Profile routes for V2.

- POST /profiles – create profile for current user (one‑to‑one).
- GET /profiles/me – retrieve current user's profile.
- PUT /profiles/me – update current user's profile.
- GET /profiles/{id} – public retrieval (visibility rules can be added later).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.models.profile import Profile, Interest, profile_interests
from app.models.user import User
from app.schemas.profile import ProfileCreate, ProfileRead, ProfileUpdate
from app.core.database import get_db
from app.api.dependencies import get_current_user

router = APIRouter(prefix="/profiles", tags=["profiles"])

def _calculate_completion(profile: Profile) -> int:
    """Calculate completion percentage based on weighted fields.
    We follow the weighting from the spec (total 100). Missing optional fields get 0.
    """
    weights = {
        "name": 20,
        "age": 15,
        "bio": 15,
        "interests": 15,
        "location": 10,
        "profile_picture": 15,
        # any other valid metadata could be allocated the remaining 10, but we skip.
    }
    score = 0
    if profile.name:
        score += weights["name"]
    if profile.age:
        score += weights["age"]
    if profile.bio:
        score += weights["bio"]
    if profile.interests:
        score += weights["interests"]
    if profile.location:
        score += weights["location"]
    if profile.profile_picture:
        score += weights["profile_picture"]
    # Clamp 0‑100
    return min(max(score, 0), 100)

@router.post("", response_model=ProfileRead, status_code=status.HTTP_201_CREATED)
def create_profile(payload: ProfileCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Ensure a profile does not already exist for this user
    if db.query(Profile).filter(Profile.user_id == current_user.id).first():
        raise HTTPException(status_code=400, detail="Profile already exists for this user")
    # Resolve interests – create if they do not exist
    interest_objs = []
    for name in payload.interests or []:
        interest = db.query(Interest).filter(Interest.name == name).first()
        if not interest:
            interest = Interest(name=name)
            db.add(interest)
            db.flush()  # assign id
        interest_objs.append(interest)
    profile = Profile(
        user_id=current_user.id,
        name=payload.name,
        age=payload.age,
        bio=payload.bio,
        location=payload.location,
        profile_picture=payload.profile_picture,
        interests=interest_objs,
    )
    # Calculate completion
    profile.completion_percentage = _calculate_completion(profile)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/me", response_model=ProfileRead)
def read_my_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

@router.put("/me", response_model=ProfileRead)
def update_my_profile(payload: ProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Update fields if provided
    if payload.name is not None:
        profile.name = payload.name
    if payload.age is not None:
        profile.age = payload.age
    if payload.bio is not None:
        profile.bio = payload.bio
    if payload.location is not None:
        profile.location = payload.location
    if payload.profile_picture is not None:
        profile.profile_picture = payload.profile_picture
    if payload.interests is not None:
        # Reset interests list
        interest_objs = []
        for name in payload.interests:
            interest = db.query(Interest).filter(Interest.name == name).first()
            if not interest:
                interest = Interest(name=name)
                db.add(interest)
                db.flush()
            interest_objs.append(interest)
        profile.interests = interest_objs
    # Re‑calculate completion
    profile.completion_percentage = _calculate_completion(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/{profile_id}", response_model=ProfileRead)
def read_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(Profile).filter(Profile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile

