"""V6 -- Block service.

Handles blocking / unblocking users and listing active blocks.
"""

import logging
from typing import List

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.blocks import Block
from app.models.reports import Report

logger = logging.getLogger(__name__)


def block_user(
    db: Session,
    blocker_id: int,
    blocked_id: int,
    reason: str = None,
) -> Block:
    """Create a block relationship between two users.

    Raises ``ValueError`` if the user tries to block themselves or if
    the block already exists.
    """
    if blocker_id == blocked_id:
        raise ValueError("You cannot block yourself.")

    block = Block(
        blocker_id=blocker_id,
        blocked_id=blocked_id,
        reason=reason,
    )
    db.add(block)
    try:
        db.commit()
        db.refresh(block)
    except IntegrityError:
        db.rollback()
        raise ValueError("You have already blocked this user.")

    logger.info("Block created: blocker=%d blocked=%d", blocker_id, blocked_id)
    return block


def unblock_user(db: Session, blocker_id: int, blocked_id: int) -> bool:
    """Remove a block relationship.

    Returns ``True`` if a block was removed, ``False`` if no matching
    block existed.
    """
    affected = (
        db.query(Block)
        .filter(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id)
        .delete(synchronize_session=False)
    )
    db.commit()
    if affected:
        logger.info("Block removed: blocker=%d blocked=%d", blocker_id, blocked_id)
    return affected > 0


def list_blocks(db: Session, user_id: int) -> List[Block]:
    """List all users that *user_id* has blocked."""
    return (
        db.query(Block)
        .filter(Block.blocker_id == user_id)
        .order_by(Block.created_at.desc())
        .all()
    )


def is_blocked(db: Session, blocker_id: int, blocked_id: int) -> bool:
    """Return ``True`` if *blocker_id* has blocked *blocked_id*."""
    return (
        db.query(Block)
        .filter(Block.blocker_id == blocker_id, Block.blocked_id == blocked_id)
        .first() is not None
    )


def list_blocked_users(db: Session, user_id: int) -> List[int]:
    """Return a list of user IDs that *user_id* has blocked."""
    rows = (
        db.query(Block.blocked_id)
        .filter(Block.blocker_id == user_id)
        .all()
    )
    return [row[0] for row in rows]
