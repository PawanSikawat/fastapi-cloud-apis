from unittest.mock import AsyncMock, patch

from httpx import AsyncClient


class TestGeneratePDF:
    async def test_raw_html_returns_pdf(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake content",
        ):
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "raw", "content": "<html><body>Hello</body></html>"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        assert "attachment" in response.headers["content-disposition"]
        assert response.content == b"%PDF-1.4 fake content"

    async def test_url_source_returns_pdf(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 url content",
        ):
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "url", "content": "https://example.com"},
            )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

    async def test_invalid_source_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "file", "content": "test"},
        )
        assert response.status_code == 422

    async def test_empty_content_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw", "content": ""},
        )
        assert response.status_code == 422

    async def test_missing_content_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw"},
        )
        assert response.status_code == 422

    async def test_url_with_file_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "file:///etc/passwd"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_url_with_javascript_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "javascript:alert(1)"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_url_with_data_scheme_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "url", "content": "data:text/html,<h1>hi</h1>"},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "INVALID_URL"

    async def test_content_too_large(self, client: AsyncClient) -> None:
        large_content = "x" * (5 * 1024 * 1024 + 1)
        response = await client.post(
            "/v1/generate/pdf",
            json={"source": "raw", "content": large_content},
        )
        assert response.status_code == 422
        data = response.json()
        assert data["error"] == "CONTENT_TOO_LARGE"

    async def test_custom_options_forwarded(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake",
        ) as mock_gen:
            response = await client.post(
                "/v1/generate/pdf",
                json={
                    "source": "raw",
                    "content": "<html>test</html>",
                    "options": {
                        "format": "Letter",
                        "orientation": "landscape",
                        "scale": 0.5,
                    },
                },
            )
        assert response.status_code == 200
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["options"].format == "Letter"
        assert call_kwargs["options"].orientation == "landscape"
        assert call_kwargs["options"].scale == 0.5

    async def test_default_options_when_omitted(self, client: AsyncClient) -> None:
        with patch(
            "pdf_from_html.routes.generate.generate",
            new_callable=AsyncMock,
            return_value=b"%PDF-1.4 fake",
        ) as mock_gen:
            response = await client.post(
                "/v1/generate/pdf",
                json={"source": "raw", "content": "<html>test</html>"},
            )
        assert response.status_code == 200
        call_kwargs = mock_gen.call_args.kwargs
        assert call_kwargs["options"].format == "A4"
        assert call_kwargs["options"].orientation == "portrait"

    async def test_invalid_scale_rejected(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/pdf",
            json={
                "source": "raw",
                "content": "<html>test</html>",
                "options": {"scale": 3.0},
            },
        )
        assert response.status_code == 422


class TestHealthCheck:
    async def test_health(self, client: AsyncClient) -> None:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
