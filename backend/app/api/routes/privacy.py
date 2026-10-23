"""V5 — Privacy Guardian routes.

- POST /privacy/check       Scan a message for sensitive information (requires auth)
- GET  /privacy/alerts      Retrieve the authenticated user's alerts (requires auth)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.privacy_alert import PrivacyAlert
from app.schemas.privacy_alert import (
    PrivacyCheckRequest,
    PrivacyResult,
    PrivacyAlertRead,
)
from app.services.privacy_guardian import detect_sensitive_info, _truncate_excerpt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.post("/check", response_model=PrivacyResult)
def check_privacy(
    payload: PrivacyCheckRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Scan a user message for sensitive information before sending.

    Requires a valid JWT bearer token (V5-14).

    Returns a structured :class:`PrivacyResult` with ``flagged``,
    ``risk_level``, ``detected_types``, ``warning``, and ``recommendation``.
    """
    result = detect_sensitive_info(payload.message)

    # Persist a privacy alert when sensitive info is detected (V5-13)
    if result.flagged:
        alert = PrivacyAlert(
            user_id=current_user.id,
            detected_types=",".join(result.detected_types),
            flagged=result.flagged,
            risk_level=result.risk_level,
            warning=result.warning,
            recommendation=result.recommendation,
            message_excerpt=_truncate_excerpt(payload.message),
        )
        db.add(alert)
        db.commit()
        db.refresh(alert)

    return result


@router.get("/alerts", response_model=list[PrivacyAlertRead])
def list_privacy_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve all privacy alerts for the authenticated user.

    Only returns the calling user's own alerts (V5-14 — user isolation).
    """
    alerts = (
        db.query(PrivacyAlert)
        .filter(PrivacyAlert.user_id == current_user.id)
        .order_by(PrivacyAlert.created_at.desc())
        .all()
    )

    # Parse the stored JSON-array strings back to lists
    for alert in alerts:
        alert.detected_types = (
            alert.detected_types.split(",") if alert.detected_types else []
        )

    return alerts
