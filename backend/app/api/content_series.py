from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.models.content_series import ContentSeries
from app.schemas.content_series import ContentSeriesCreate, ContentSeriesResponse

router = APIRouter(prefix="/content-series", tags=["content-series"])


@router.post("", response_model=ContentSeriesResponse, status_code=status.HTTP_201_CREATED)
async def create_content_series(
    data: ContentSeriesCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    series = ContentSeries(
        name=data.name,
        root_scheduled_at=data.root_scheduled_at,
        owner_id=user_id,
    )
    db.add(series)
    await db.commit()
    await db.refresh(series)
    return series
