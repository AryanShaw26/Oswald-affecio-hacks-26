"""V4 — Conversation Safety routes.

- POST /safety/analyze        Analyze a message for safety risks (requires auth)
- GET  /safety/conversations/{id}
                              Retrieve an authorised safety analysis (requires auth)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.conversation_safety import ConversationSafety
from app.schemas.conversation_safety import (
    ConversationSafetyRequest,
    ConversationSafetyResult,
    ConversationSafetyRead,
)
from app.services.conversation_safety import analyze_message, _truncate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/safety", tags=["safety"])


@router.post("/analyze", response_model=ConversationSafetyResult)
def analyze_safety(
    payload: ConversationSafetyRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze a user message for conversation-safety risks.

    Requires a valid JWT bearer token (V4-V4-15).

    Returns a structured :class:`ConversationSafetyResult` with
    ``risk_level``, ``categories``, ``flagged``, ``summary``, and
    ``recommendation``.
    """
    result = analyze_message(payload.message, user_id=current_user.id)

    # Persist the analysis for audit / history (V4-17)
    analysis = ConversationSafety(
        user_id=current_user.id,
        message_snippet=_truncate(payload.message, limit=500),
        risk_level=result["risk_level"],
        categories=",".join(result["categories"]),
        flagged=result["flagged"],
        summary=result["summary"],
        recommendation=result["recommendation"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Return only the structured result — never the raw JWT or message
    return result


@router.get("/conversations/{conversation_id}", response_model=ConversationSafetyRead)
def get_safety_analysis(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve a stored safety analysis.

    Only the owning user may retrieve their own analysis (V4-16 — user isolation).
    """
    analysis = db.query(ConversationSafety).filter(
        ConversationSafety.id == conversation_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    if analysis.user_id != current_user.id:
        # Do not leak existence — return 404 rather than 403
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found",
        )

    # Parse the stored JSON-array string back to a list
    analysis.categories = analysis.categories.split(",") if analysis.categories else []
    return analysis
