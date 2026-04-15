from typing import Annotated

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import timedelta

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


async def check_scheduling_conflict(
    db: AsyncSession,
    user_id: int,
    platform: str,
    scheduled_at: datetime,
) -> None:
    """
    Raises HTTPException if there's a scheduling conflict within 15 minutes.
    """

    MIN_TIME_GAP = timedelta(minutes=15)

    min_time = scheduled_at - MIN_TIME_GAP
    max_time = scheduled_at + MIN_TIME_GAP

    conflict = await db.scalar(
        select(ContentSeriesPost.scheduled_at)
        .join(Post, Post.id == ContentSeriesPost.post_id)
        .where(Post.platform == platform)
        .join(ContentSeries, ContentSeries.id == ContentSeriesPost.series_id)
        .where(ContentSeries.owner_id == user_id)
        .where(ContentSeriesPost.scheduled_at >= min_time)
        .where(ContentSeriesPost.scheduled_at <= max_time)
        .limit(1)  # We only care if at least one exists
    )

    if conflict is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Post on {platform} at {scheduled_at.isoformat()} "
                f"is within 15 minutes of an existing post at {conflict.isoformat()}."
            ),
        )


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


    # @note verify post exists
    post_result = await db.execute(select(Post).where(Post.id == data.post_id))
    post = post_result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


    # @note verify there isn't a scheduling conflict on the same platform
    await check_scheduling_conflict(
        db=db,
        user_id=user_id,
        platform=post.platform,
        scheduled_at=data.scheduled_at,
    )

    # @note create the series post
    entry = ContentSeriesPost(
        series_id=series_id,
        post_id=data.post_id,
        position=data.position,
        scheduled_at=data.scheduled_at,
    )
    db.add(entry)
    await db.commit()

    # @note return the updated series
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
