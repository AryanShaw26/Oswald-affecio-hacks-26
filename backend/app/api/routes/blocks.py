"""V6 -- Block routes.

POST   /blocks                 -- block a user
GET    /blocks                 -- list all users the current user has blocked
DELETE /blocks/{target_id}     -- unblock a user
GET    /blocks/check/{target_id} -- check if a user is blocked
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from sqlalchemy.orm import Session
from app.core.database import get_db

from app.api.dependencies import get_current_user
from app.schemas.blocks import BlockCreate, BlockRead, BlockResponse
from app.services.blocks import (
    block_user,
    unblock_user,
    list_blocks,
    is_blocked,
    list_blocked_users,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blocks", tags=["blocks"])


@router.post("/", response_model=BlockResponse, status_code=status.HTTP_201_CREATED)
def create_block(
    payload: BlockCreate,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Block another user."""
    try:
        block = block_user(
            db=db,
            blocker_id=current_user.id,
            blocked_id=payload.blocked_user_id,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    # Create a confirmation alert for the blocker
    try:
        from app.services.alerts import create_alert
        create_alert(
            db=db,
            user_id=current_user.id,
            alert_type="block_applied",
            severity="medium",
            message=f"You have blocked user ID {payload.blocked_user_id}. "
                    f"They will no longer appear in your results.",
            related_block_id=block.id,
        )
    except Exception:
        logger.exception("Failed to create alert for block %d", block.id)

    return {
        "id": block.id,
        "message": f"User {payload.blocked_user_id} has been blocked.",
        "created_at": block.created_at,
    }


@router.get("/", response_model=list[BlockRead])
def list_user_blocks(
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all users the current user has blocked."""
    return list_blocks(db, current_user.id)


@router.get("/check/{target_id}", response_model=dict)
def check_block(
    target_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Check whether *target_id* is blocked by the current user."""
    blocked = is_blocked(db, current_user.id, target_id)
    return {"target_id": target_id, "is_blocked": blocked}


@router.delete("/{target_id}", response_model=dict)
def delete_block(
    target_id: int,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Unblock a previously blocked user."""
    removed = unblock_user(db, current_user.id, target_id)
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found or you have not blocked this user.",
        )
    return {"message": f"User {target_id} has been unblocked."}


@router.get("/ids", response_model=list[int])
def get_blocked_ids(
    current_user=Depends(get_current_user),
    db: Session =Depends(get_db),
):
    """Return a simple list of blocked user IDs (useful for frontend filtering)."""
    return list_blocked_users(db, current_user.id)
