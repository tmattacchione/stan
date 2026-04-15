from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.schemas.post import PostResponse


class ContentSeriesCreate(BaseModel):
    name: str
    root_scheduled_at: datetime


class ContentSeriesResponse(BaseModel):
    id: int
    name: str
    root_scheduled_at: datetime
    owner_id: int
    created_at: Optional[datetime] = None
    posts: List[ContentSeriesPostEntry] = []

    model_config = ConfigDict(from_attributes=True)


class ContentSeriesPostEntry(BaseModel):
    id: int
    position: int
    scheduled_at: Optional[datetime] = None
    post: Optional[PostResponse] = None

    model_config = ConfigDict(from_attributes=True)


class ContentSeriesPostAdd(BaseModel):
    post_id: int
    position: int
    scheduled_at: datetime
