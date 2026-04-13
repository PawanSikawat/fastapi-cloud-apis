from httpx import AsyncClient


class TestLoginPage:
    async def test_login_page_renders(self, client: AsyncClient) -> None:
        response = await client.get("/ui/login")
        assert response.status_code == 200
        assert "Enter your API Key" in response.text

    async def test_login_with_valid_key(self, client: AsyncClient, app) -> None:  # type: ignore[no-untyped-def]
        api_key = app.state._test_api_key  # noqa: SLF001
        response = await client.post(
            "/ui/login",
            data={"api_key": api_key},
            follow_redirects=False,
        )
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/"
        assert "api_key" in response.headers.get("set-cookie", "")

    async def test_login_with_invalid_key(self, client: AsyncClient) -> None:
        response = await client.post(
            "/ui/login",
            data={"api_key": "sk_invalid_key"},
            follow_redirects=False,
        )
        assert response.status_code == 200
        assert "Invalid API key" in response.text


class TestLogout:
    async def test_logout_redirects(self, client: AsyncClient) -> None:
        response = await client.post("/ui/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/ui/login"


class TestGeneratePage:
    async def test_generate_page_renders(self, client: AsyncClient) -> None:
        response = await client.get("/ui/")
        assert response.status_code == 200
        assert "Generate QR Code" in response.text
