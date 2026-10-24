"""V6 -- Report routes.

POST   /reports            -- create a new report
GET    /reports/user/{user_id} -- list reports against a user
GET    /reports            -- list reports filed by the current user
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from app.core.database import get_db

from app.api.dependencies import get_current_user
from app.schemas.reports import ReportCreate, ReportRead
from app.services.reports import create_report, list_reports_for_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
def submit_report(
    payload: ReportCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a report against another user.

    Automatically creates a confirmation *alert* for the reporter and
   , if the reported user has been blocked by the reporter, links the
    report to that block.
    """
    try:
        report = create_report(
            db=db,
            reporter_id=current_user.id,
            reported_user_id=payload.reported_user_id,
            report_type=payload.report_type,
            description=payload.description,
            profile_id=payload.profile_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Create a confirmation alert for the reporter
    try:
        from app.services.alerts import create_alert
        create_alert(
            db=db,
            user_id=current_user.id,
            alert_type="report_created",
            severity="low",
            message=f"Your report (ID {report.id}) has been received and is pending review.",
            related_report_id=report.id,
        )
    except Exception:
        # Alert creation should never fail the report
        logger.exception("Failed to create alert for report %d", report.id)

    return report


@router.get("/user/{user_id}", response_model=list[ReportRead])
def list_user_reports(
    user_id: int,
    current_user=Depends(get_current_user),
    db: Session =Depends(get_db),
):
    """List reports against a specific user.

    A user can only see reports where they are the *target*
    (reported_user_id matches).  This is enforced in the service layer.
    """
    # Only the reported user can see their own reports
    if user_id != current_user.id:
        # Allow admin / moderator role to view any user's reports
        if not getattr(current_user, "is_admin", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own reports.",
            )

    reports = list_reports_for_user(db, user_id, include_reported=True)
    return reports


@router.get("/mine", response_model=list[ReportRead])
def list_my_reports(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List reports that the current user has filed."""
    return list_reports_for_user(db, current_user.id, include_reported=False)
