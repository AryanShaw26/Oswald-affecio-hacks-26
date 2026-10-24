"""V6 -- Alert service.

Handles retrieval of safety alerts and creation of system-generated
alert notifications.
"""

import logging
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.alerts import Alert, VALID_ALERT_TYPES, VALID_ALERT_SEVERITIES

logger = logging.getLogger(__name__)


def create_alert(
    db: Session,
    user_id: int,
    alert_type: str,
    severity: str,
    message: str,
    related_report_id: Optional[int] = None,
    related_block_id: Optional[int] = None,
) -> Alert:
    """Create a system or user-facing alert for *user_id*.

    Typically called after a report or block is created so the reporter
    receives a confirmation / follow-up notification.
    """
    if alert_type not in VALID_ALERT_TYPES:
        raise ValueError(f"Invalid alert_type: {alert_type}")

    if severity not in VALID_ALERT_SEVERITIES:
        raise ValueError(f"Invalid severity: {severity}")

    alert = Alert(
        user_id=user_id,
        alert_type=alert_type,
        severity=severity,
        message=message,
        is_read=False,
        related_report_id=related_report_id,
        related_block_id=related_block_id,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    logger.info(
        "Alert created: id=%d user=%d type=%s severity=%s",
        alert.id,
        user_id,
        alert_type,
        severity,
    )
    return alert


def get_alerts(
    db: Session,
    user_id: int,
    *,
    only_unread: bool = False,
    limit: int = 50,
) -> List[Alert]:
    """Retrieve alerts for a user, optionally only unread ones."""
    query = db.query(Alert).filter(Alert.user_id == user_id)

    if only_unread:
        query = query.filter(Alert.is_read == False)  # noqa: E712

    query = query.order_by(Alert.created_at.desc()).limit(limit)
    return query.all()


def mark_alerts_read(db: Session, user_id: int) -> int:
    """Mark all unread alerts for *user_id* as read.

    Returns the number of alerts updated.
    """
    updated = (
        db.query(Alert)
        .filter(Alert.user_id == user_id, Alert.is_read == False)  # noqa: E712
        .update({"is_read": True}, synchronize_session=False)
    )
    db.commit()
    return updated


def count_unread_alerts(db: Session, user_id: int) -> int:
    """Count unread alerts for *user_id*."""
    return (
        db.query(Alert)
        .filter(Alert.user_id == user_id, Alert.is_read == False)  # noqa: E712
        .count()
    )


def get_alert(db: Session, alert_id: int, user_id: int) -> Optional[Alert]:
    """Fetch a single alert by id with ownership check."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if alert and alert.user_id != user_id:
        return None
    return alert
