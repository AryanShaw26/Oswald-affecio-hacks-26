"""V6 -- Dashboard route.

GET /dashboard -- aggregated safety dashboard for the authenticated user.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from app.core.database import get_db

from app.api.dependencies import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard import get_dashboard_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardResponse)
def dashboard(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return an aggregated safety dashboard for the current user.

    Includes trust score, recent alerts, recent reports, and block counts.
    """
    try:
        data = get_dashboard_data(db, current_user.id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return data
