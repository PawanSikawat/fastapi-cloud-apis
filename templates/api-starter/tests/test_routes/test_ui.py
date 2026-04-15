from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeSerializer

from template_api.middleware.cookie_auth import CookieToHeaderMiddleware

COOKIE_SECRET = "test-cookie-secret"
SIGNER = URLSafeSerializer(COOKIE_SECRET, salt="api-key")


@pytest.fixture
async def ui_client(app) -> AsyncClient:  # type: ignore[no-untyped-def]
    wrapped = CookieToHeaderMiddleware(app, secret_key=COOKIE_SECRET)
    transport = ASGITransport(app=wrapped)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def test_login_page_renders(ui_client: AsyncClient) -> None:
    response = await ui_client.get("/ui/login")
    assert response.status_code == 200
    assert "Starter API Login" in response.text


async def test_dashboard_requires_auth(ui_client: AsyncClient) -> None:
    response = await ui_client.get("/ui/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/ui/login"


async def test_dashboard_renders_for_authenticated_user(
    ui_client: AsyncClient, app: MagicMock
) -> None:
    api_key = app.state._test_api_key  # noqa: SLF001
    signed = SIGNER.dumps(api_key)
    ui_client.cookies.set("api_key", signed)

    response = await ui_client.get("/ui/")
    assert response.status_code == 200
    assert "Starter API Dashboard" in response.text
