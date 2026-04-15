import pytest
from httpx import AsyncClient

# @note convenience
async def create_series_and_post(client: AsyncClient, headers: dict, platform: str, scheduled_at: str) -> tuple[int, int, int]:
    """Helper — creates a series, a post, adds the post to the series.
    Returns (series_id, post_id, entry_id)."""
    # create series
    r = await client.post(
            "/api/content-series",
            headers=headers,
            json={"name": "Test Series", "root_scheduled_at": scheduled_at},
            )
    assert r.status_code == 201
    series_id = r.json()["id"]

    # create post
    r = await client.post(
            "/api/posts",
            headers=headers,
            json={"title": "Test Post", "platform": platform, "status": "draft"},
            )
    assert r.status_code == 201
    post_id = r.json()["id"]

    # add post to series
    r = await client.post(
            f"/api/content-series/{series_id}/posts",
            headers=headers,
            json={"post_id": post_id, "position": 1, "scheduled_at": scheduled_at},
            )
    assert r.status_code == 201

    return series_id, post_id


@pytest.mark.asyncio
async def test_15_minute_conflict_same_platform(client: AsyncClient, auth_headers: dict):
    """
    Adding a post to a series should fail with 409 if another post on the
    same platform is already scheduled within 15 minutes.
    """
    platform = "instagram"
    first_slot = "2025-06-01T09:00:00Z"
    conflicting_slot = "2025-06-01T09:10:00Z"  # 10 min later — within 15 min window

    # Set up first series + post
    await create_series_and_post(client, auth_headers, platform, first_slot)

    # Create a second series and post that conflicts
    r = await client.post(
            "/api/content-series",
            headers=auth_headers,
            json={"name": "Conflicting Series", "root_scheduled_at": conflicting_slot},
            )
    series_2_id = r.json()["id"]

    r = await client.post(
            "/api/posts",
            headers=auth_headers,
            json={"title": "Conflicting Post", "platform": platform, "status": "draft"},
            )
    post_2_id = r.json()["id"]
    # This should fail
    r = await client.post(
        f"/api/content-series/{series_2_id}/posts",
        headers=auth_headers,
        json={"post_id": post_2_id, "position": 1, "scheduled_at": conflicting_slot},
    )
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_15_minute_conflict_different_platform(client: AsyncClient, auth_headers: dict):
    """
    Same time slot on a different platform should be allowed.
    TODO: revisit if constraint becomes global across all platforms.
    """
    slot = "2025-06-01T09:00:00Z"

    await create_series_and_post(client, auth_headers, "instagram", slot)

    # Second series on a different platform at the same time
    r = await client.post(
        "/api/content-series",
        headers=auth_headers,
        json={"name": "LinkedIn Series", "root_scheduled_at": slot},
    )
    series_2_id = r.json()["id"]

    r = await client.post(
        "/api/posts",
        headers=auth_headers,
        json={"title": "LinkedIn Post", "platform": "linkedin", "status": "draft"},
    )
    post_2_id = r.json()["id"]

    r = await client.post(
        f"/api/content-series/{series_2_id}/posts",
        headers=auth_headers,
        json={"post_id": post_2_id, "position": 1, "scheduled_at": slot},
    )
    assert r.status_code == 201
