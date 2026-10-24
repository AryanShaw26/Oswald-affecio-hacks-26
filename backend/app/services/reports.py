"""V6 -- Report service.

Handles creation and listing of user-submitted reports.
"""

import json
import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.reports import Report, VALID_REPORT_TYPES

logger = logging.getLogger(__name__)


def create_report(
    db: Session,
    reporter_id: int,
    reported_user_id: int,
    report_type: str,
    description: str,
    profile_id: Optional[int] = None,
    evidence: Optional[dict] = None,
) -> Report:
    """Create a new report.

    Validates the report type, builds an evidence JSON blob (which may
    include auto-detected signals such as trust-score or privacy-alert
    data at creation time), and persists the record.

    Raises ``ValueError`` if the report type is invalid or the
    reporter and reported user are the same person.
    """
    if report_type not in VALID_REPORT_TYPES:
        raise ValueError(f"Invalid report_type: {report_type}")

    if reporter_id == reported_user_id:
        raise ValueError("You cannot report yourself.")

    # Build evidence JSON if provided
    evidence_str = json.dumps(evidence) if evidence else None

    report = Report(
        reporter_id=reporter_id,
        reported_user_id=reported_user_id,
        profile_id=profile_id,
        report_type=report_type,
        description=description,
        evidence=evidence_str,
        status="pending",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    logger.info(
        "Report created: id=%d reporter=%d reported=%s type=%s",
        report.id,
        reporter_id,
        reported_user_id,
        report_type,
    )

    return report


def list_reports_for_user(
    db: Session,
    user_id: int,
    *,
    include_reported: bool = True,
    limit: int = 50,
) -> List[Report]:
    """List reports for a given user.

    By default returns reports where the user is the *target*
    (reported_user_id == user_id).  If ``include_reported`` is ``False``
    only reports filed *by* the user (reporter_id == user_id) are returned.
    """
    query = db.query(Report)
    if include_reported:
        # User is the target of the report (most common use-case for safety)
        query = query.filter(Report.reported_user_id == user_id)
    else:
        # User filed the report
        query = query.filter(Report.reporter_id == user_id)

    query = query.order_by(Report.created_at.desc()).limit(limit)
    return query.all()


def get_report(db: Session, report_id: int, user_id: int) -> Optional[Report]:
    """Fetch a single report by id, ensuring ownership isolation.

    The caller must be either the reporter or the reported user.
    """
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        return None

    if report.reporter_id != user_id and report.reported_user_id != user_id:
        # Do not leak existence — return None
        return None

    return report
