from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.database import get_db
from app.models.connection import Connection
from app.models.user import User
from app.schemas.connection import ConnectionCreate, ConnectionRead, ConnectionStatusUpdate

router = APIRouter(prefix="/connections", tags=["connections"])


@router.post("", response_model=ConnectionRead, status_code=status.HTTP_201_CREATED)
def create_connection(
    payload: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if payload.target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot connect with yourself")

    existing = (
        db.query(Connection)
        .filter(
            or_(
                and_(Connection.requester_id == current_user.id, Connection.target_user_id == payload.target_user_id),
                and_(Connection.requester_id == payload.target_user_id, Connection.target_user_id == current_user.id),
            )
        )
        .first()
    )
    if existing:
        if existing.status == "rejected":
            existing.status = "pending"
            existing.requester_id = current_user.id
            existing.target_user_id = payload.target_user_id
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(status_code=400, detail=f"Connection already exists with status '{existing.status}'")

    connection = Connection(requester_id=current_user.id, target_user_id=payload.target_user_id, status="pending")
    db.add(connection)
    db.commit()
    db.refresh(connection)
    return connection


@router.get("", response_model=list[ConnectionRead])
def list_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connections = (
        db.query(Connection)
        .filter(
            or_(
                Connection.requester_id == current_user.id,
                Connection.target_user_id == current_user.id,
            )
        )
        .order_by(Connection.created_at.desc())
        .all()
    )
    return connections


@router.get("/status/{target_user_id}", response_model=dict)
def get_connection_status(
    target_user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = (
        db.query(Connection)
        .filter(
            or_(
                and_(Connection.requester_id == current_user.id, Connection.target_user_id == target_user_id),
                and_(Connection.requester_id == target_user_id, Connection.target_user_id == current_user.id),
            )
        )
        .order_by(Connection.created_at.desc())
        .first()
    )
    if not connection:
        return {"status": "not_connected", "target_user_id": target_user_id}
    return {"status": connection.status, "target_user_id": target_user_id, "connection_id": connection.id}


@router.patch("/{connection_id}", response_model=ConnectionRead)
def update_connection_status(
    connection_id: int,
    payload: ConnectionStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    connection = db.query(Connection).filter(Connection.id == connection_id).first()
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    if connection.requester_id != current_user.id and connection.target_user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed to update this connection")

    connection.status = payload.status
    db.commit()
    db.refresh(connection)
    return connection
