"""V6 -- Dashboard service.

Aggregates trust scores, alerts, reports, and block counts for a
single user so the frontend can render a one-page safety dashboard.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.models.trust_score import TrustScore
from app.models.alerts import Alert
from app.models.reports import Report
from app.models.blocks import Block
from app.services.alerts import count_unread_alerts

logger = logging.getLogger(__name__)


def get_dashboard_data(db: Session, user_id: int) -> dict:
    """Build a dashboard payload for the authenticated user.

    Returns a plain dict that the route layer wraps into
    ``DashboardResponse``.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("User not found")

    # Most recent trust score (latest by created_at)
    latest_trust = (
        db.query(TrustScore)
        .filter(TrustScore.user_id == user_id)
        .order_by(TrustScore.created_at.desc())
        .first()
    )

    # Recent alerts (last 10)
    recent_alerts = (
        db.query(Alert)
        .filter(Alert.user_id == user_id)
        .order_by(Alert.created_at.desc())
        .limit(10)
        .all()
    )

    # Reports filed against this user (target)
    reports_against = (
        db.query(Report)
        .filter(Report.reported_user_id == user_id)
        .order_by(Report.created_at.desc())
        .limit(5)
        .all()
    )

    # Block counts
    blocks_given = db.query(Block).filter(Block.blocker_id == user_id).count()
    blocks_received = db.query(Block).filter(Block.blocked_id == user_id).count()

    # Totals
    total_reports = db.query(Report).filter(Report.reported_user_id == user_id).count()
    total_alerts = db.query(Alert).filter(Alert.user_id == user_id).count()
    unread_alerts = count_unread_alerts(db, user_id)

    return {
        "user_id": user.id,
        "user_name": user.name,
        "user_email": user.email,
        "trust_score": {
            "score": latest_trust.score if latest_trust else None,
            "risk_level": latest_trust.risk_level if latest_trust else "unknown",
            "created_at": latest_trust.created_at if latest_trust else None,
        } if latest_trust else None,
        "recent_alerts": recent_alerts,
        "recent_reports": reports_against,
        "blocks_given_count": blocks_given,
        "blocks_received_count": blocks_received,
        "reports_count": total_reports,
        "alerts_count": total_alerts,
        "unread_alerts_count": unread_alerts,
    }
