from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

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


@router.get("", response_model=list[ContentSeriesResponse])
async def list_content_series(
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.owner_id == user_id)
        .options(selectinload(ContentSeries.posts))
        .order_by(ContentSeries.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{series_id}", response_model=ContentSeriesResponse)
async def get_content_series(
    series_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.id == series_id, ContentSeries.owner_id == user_id)
        .options(selectinload(ContentSeries.posts))
    )
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    return series


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_content_series(
    series_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.id == series_id, ContentSeries.owner_id == user_id)
    )
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")
    await db.delete(series)
    await db.commit()
