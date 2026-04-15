from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ContentSeriesCreate(BaseModel):
    name: str
    root_scheduled_at: datetime


class ContentSeriesResponse(BaseModel):
    id: int
    name: str
    root_scheduled_at: datetime
    owner_id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ContentSeriesPostEntry(BaseModel):
    id: int
    post_id: int
    position: int
    scheduled_at: datetime

    class Config:
        from_attributes = True
