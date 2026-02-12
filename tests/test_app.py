import pytest
from httpx import AsyncClient, ASGITransport

from src import app as app_module


@pytest.mark.asyncio
async def test_root_redirect():
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/")
        assert r.status_code in (307, 302)
        assert r.headers.get("location") == "/static/index.html"


@pytest.mark.asyncio
async def test_get_activities():
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.get("/activities")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "Soccer Club" in data


@pytest.mark.asyncio
async def test_signup_and_unregister_cycle():
    activity = "Soccer Club"
    email = "testuser+signup@example.com"

    # Ensure clean start
    if email in app_module.activities[activity]["participants"]:
        app_module.activities[activity]["participants"].remove(email)

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Signup
        r = await ac.post(f"/activities/{activity}/signup", params={"email": email})
        assert r.status_code == 200
        assert email in app_module.activities[activity]["participants"]

        # Unregister
        r2 = await ac.post(f"/activities/{activity}/unregister", params={"email": email})
        assert r2.status_code == 200
        assert email not in app_module.activities[activity]["participants"]


@pytest.mark.asyncio
async def test_signup_duplicate_returns_400():
    activity = "Soccer Club"
    # Use existing participant from seed data
    email = "lucas@mergington.edu"

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(f"/activities/{activity}/signup", params={"email": email})
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_unregister_not_registered_returns_400():
    activity = "Soccer Club"
    email = "not-registered@example.com"

    # Ensure not present
    if email in app_module.activities[activity]["participants"]:
        app_module.activities[activity]["participants"].remove(email)

    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post(f"/activities/{activity}/unregister", params={"email": email})
        assert r.status_code == 400


@pytest.mark.asyncio
async def test_activity_not_found_returns_404():
    transport = ASGITransport(app=app_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        r = await ac.post("/activities/NoSuchActivity/signup", params={"email": "a@b.com"})
        assert r.status_code == 404
