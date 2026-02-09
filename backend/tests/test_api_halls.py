"""Integration tests for the /api/v2/halls endpoint."""

import pytest


@pytest.mark.asyncio
async def test_list_halls(client, seed_halls):
    """GET /api/v2/halls returns all 7 dining halls."""
    resp = await client.get("/api/v2/halls/")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 7


@pytest.mark.asyncio
async def test_list_halls_empty(client):
    """GET /api/v2/halls with no seed data returns an empty list."""
    resp = await client.get("/api/v2/halls/")
    assert resp.status_code == 200
    data = resp.json()
    assert data == []


@pytest.mark.asyncio
async def test_hall_response_shape(client, seed_halls):
    """Each hall has the expected fields with correct types."""
    resp = await client.get("/api/v2/halls/")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0

    hall = data[0]
    assert "id" in hall
    assert "name" in hall
    assert "college" in hall
    assert "vendor_type" in hall
    assert "color" in hall

    assert isinstance(hall["id"], str)
    assert isinstance(hall["name"], str)
    assert isinstance(hall["college"], str)
    assert isinstance(hall["vendor_type"], str)
    assert hall["color"] is None or isinstance(hall["color"], str)


@pytest.mark.asyncio
async def test_halls_ordered_by_name(client, seed_halls):
    """Halls are returned ordered alphabetically by name."""
    resp = await client.get("/api/v2/halls/")
    data = resp.json()
    names = [h["name"] for h in data]
    assert names == sorted(names)
