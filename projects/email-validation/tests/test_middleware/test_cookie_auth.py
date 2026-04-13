import pytest
from httpx import ASGITransport, AsyncClient
from itsdangerous import URLSafeSerializer
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from email_validation.middleware.cookie_auth import CookieToHeaderMiddleware

SECRET = "test-secret"
SIGNER = URLSafeSerializer(SECRET, salt="api-key")


def _echo_header_app(request: Request) -> PlainTextResponse:
    """Test app that echoes back the x-api-key header value."""
    value = request.headers.get("x-api-key", "MISSING")
    return PlainTextResponse(value)


def _build_app() -> Starlette:
    app = Starlette(
        routes=[
            Route("/api/test", _echo_header_app),
            Route("/ui/", _echo_header_app),
            Route("/ui/login", _echo_header_app),
        ],
    )
    app.add_middleware(CookieToHeaderMiddleware, secret_key=SECRET)
    return app


@pytest.fixture
def test_app() -> Starlette:
    return _build_app()


@pytest.fixture
async def client(test_app: Starlette) -> AsyncClient:
    transport = ASGITransport(app=test_app)
    return AsyncClient(transport=transport, base_url="http://test")


class TestCookieInjection:
    async def test_valid_cookie_injects_header(self, client: AsyncClient) -> None:
        signed = SIGNER.dumps("pk_test_abc123")
        response = await client.get("/api/test", cookies={"api_key": signed})
        assert response.text == "pk_test_abc123"

    async def test_invalid_cookie_does_not_inject_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/test", cookies={"api_key": "tampered-value"})
        assert response.text == "MISSING"

    async def test_no_cookie_no_header(self, client: AsyncClient) -> None:
        response = await client.get("/api/test")
        assert response.text == "MISSING"

    async def test_existing_header_not_overridden(self, client: AsyncClient) -> None:
        signed = SIGNER.dumps("pk_from_cookie")
        response = await client.get(
            "/api/test",
            headers={"x-api-key": "pk_from_header"},
            cookies={"api_key": signed},
        )
        assert response.text == "pk_from_header"


class TestUIRedirect:
    async def test_ui_path_without_cookie_redirects_to_login(self, client: AsyncClient) -> None:
        response = await client.get("/ui/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"

    async def test_login_page_not_redirected(self, client: AsyncClient) -> None:
        response = await client.get("/ui/login")
        assert response.status_code == 200

    async def test_ui_path_with_valid_cookie_passes_through(self, client: AsyncClient) -> None:
        signed = SIGNER.dumps("pk_test_key")
        response = await client.get("/ui/", cookies={"api_key": signed})
        assert response.status_code == 200
        assert response.text == "pk_test_key"

    async def test_ui_path_with_invalid_cookie_redirects_to_login(
        self, client: AsyncClient
    ) -> None:
        response = await client.get("/ui/", cookies={"api_key": "bad"}, follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/ui/login"

    async def test_non_ui_path_without_cookie_no_redirect(self, client: AsyncClient) -> None:
        response = await client.get("/api/test")
        assert response.status_code == 200
        assert response.text == "MISSING"
