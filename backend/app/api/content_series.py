from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user_id
from app.core.database import get_db
from app.models.content_series import ContentSeries
from app.schemas.content_series import ContentSeriesCreate, ContentSeriesResponse
from app.models.content_series_post import ContentSeriesPost
from app.models.post import Post
from app.schemas.content_series import ContentSeriesPostAdd

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


@router.post("/{series_id}/posts", response_model=ContentSeriesResponse, status_code=status.HTTP_201_CREATED)
async def add_post_to_series(
    series_id: int,
    data: ContentSeriesPostAdd,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    # @note verify series exists and belongs to user
    result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.id == series_id, ContentSeries.owner_id == user_id)
        .options(selectinload(ContentSeries.posts))
    )
    series = result.scalar_one_or_none()
    if not series:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")

    # @todo check post belongs to current user
    post_result = await db.execute(select(Post).where(Post.id == data.post_id))
    if not post_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    entry = ContentSeriesPost(
        series_id=series_id,
        post_id=data.post_id,
        position=data.position,
        scheduled_at=data.scheduled_at,
    )
    db.add(entry)
    await db.commit()

    result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.id == series_id)
        .options(selectinload(ContentSeries.posts))
    )
    return result.scalar_one()


@router.delete("/{series_id}/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_post_from_series(
    series_id: int,
    post_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: Annotated[int, Depends(get_current_user_id)],
):
    # Confirm series exists and belongs to user
    series_result = await db.execute(
        select(ContentSeries)
        .where(ContentSeries.id == series_id, ContentSeries.owner_id == user_id)
    )
    if not series_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Series not found")

    entry_result = await db.execute(
        select(ContentSeriesPost)
        .where(ContentSeriesPost.series_id == series_id, ContentSeriesPost.post_id == post_id)
    )
    entry = entry_result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not in series")

    await db.delete(entry)
    await db.commit()
