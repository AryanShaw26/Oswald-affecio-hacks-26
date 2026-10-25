from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ConnectionCreate(BaseModel):
    target_user_id: int = Field(..., gt=0)


class ConnectionStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|accepted|rejected)$")


class ConnectionRead(BaseModel):
    id: int
    requester_id: int
    target_user_id: int
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
