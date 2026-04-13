from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeSerializer

from pdf_from_html.middleware.cookie_auth import CookieToHeaderMiddleware

COOKIE_SECRET = "test-cookie-secret"
SIGNER = URLSafeSerializer(COOKIE_SECRET, salt="api-key")


@pytest.fixture
async def ui_client(app) -> AsyncClient:  # type: ignore[no-untyped-def]
    """HTTP client without API key header -- uses cookies like a browser."""
    # Wrap the app with CookieToHeaderMiddleware for realistic testing
    wrapped = CookieToHeaderMiddleware(app, secret_key=COOKIE_SECRET)
    transport = ASGITransport(app=wrapped)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestLoginPage:
    async def test_get_login_renders_form(self, ui_client: AsyncClient) -> None:
        response = await ui_client.get("/ui/login")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "API Key" in response.text

    async def test_post_login_valid_key_sets_cookie_and_redirects(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        api_key = app.state._test_api_key  # noqa: SLF001
        response = await ui_client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/"
        assert "api_key" in response.cookies

    async def test_post_login_invalid_key_shows_error(self, ui_client: AsyncClient) -> None:
        response = await ui_client.post(
            "/ui/login",
            data={"api_key": "pk_invalid_key_12345678"},
        )
        assert response.status_code == 200
        assert "Invalid" in response.text or "invalid" in response.text


class TestLogout:
    async def test_logout_clears_cookie_and_redirects(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        # First login to get a cookie
        api_key = app.state._test_api_key  # noqa: SLF001
        login_resp = await ui_client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )

        # Transfer login cookie to client jar for subsequent requests
        ui_client.cookies.update(login_resp.cookies)

        response = await ui_client.post(
            "/ui/logout",
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/login"
        # Cookie should be cleared (max_age=0)
        assert "api_key" in response.headers.get("set-cookie", "")


class TestGeneratePage:
    async def test_authenticated_user_sees_generate_form(
        self, ui_client: AsyncClient, app: MagicMock
    ) -> None:
        api_key = app.state._test_api_key  # noqa: SLF001
        signed = SIGNER.dumps(api_key)
        ui_client.cookies.set("api_key", signed)
        response = await ui_client.get("/ui/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Generate PDF" in response.text

    async def test_unauthenticated_user_redirected_to_login(self, ui_client: AsyncClient) -> None:
        response = await ui_client.get("/ui/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"
