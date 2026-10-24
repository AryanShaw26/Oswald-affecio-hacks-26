"""V6 -- Safety Alerts routes.

GET    /alerts                      -- list current user's alerts
GET    /alerts/unread               -- list only unread alerts
GET    /alerts/unread-count         -- count of unread alerts
POST   /alerts/read                 -- mark all alerts as read
GET    /alerts/{alert_id}           -- get a single alert
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from app.core.database import get_db

from app.api.dependencies import get_current_user
from app.schemas.alerts import AlertRead, AlertResponse
from app.services.alerts import get_alerts, mark_alerts_read, count_unread_alerts, get_alert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("/", response_model=list[AlertRead])
def list_alerts(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all alerts for the current user (most recent first)."""
    return get_alerts(db, current_user.id)


@router.get("/unread", response_model=list[AlertRead])
def list_unread_alerts(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List only unread alerts for the current user."""
    return get_alerts(db, current_user.id, only_unread=True)


@router.get("/unread-count", response_model=dict)
def unread_count(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the number of unread alerts for the current user."""
    count = count_unread_alerts(db, current_user.id)
    return {"unread_count": count}


@router.post("/read", response_model=dict)
def mark_all_read(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark all alerts for the current user as read."""
    updated = mark_alerts_read(db, current_user.id)
    return {"message": f"Marked {updated} alert(s) as read."}


@router.get("/{alert_id}", response_model=AlertRead)
def get_single_alert(
    alert_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve a single alert by ID."""
    alert = get_alert(db, alert_id, current_user.id)
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    return alert
