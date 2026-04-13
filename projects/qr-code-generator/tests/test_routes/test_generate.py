import io

from httpx import AsyncClient
from PIL import Image


class TestGenerateQRCodeHappyPath:
    async def test_minimal_request_returns_png(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com"},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

    async def test_svg_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com", "format": "svg"},
        )
        assert response.status_code == 200
        assert "image/svg+xml" in response.headers["content-type"]
        assert b"<svg" in response.content

    async def test_custom_colors(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={
                "data": "test",
                "foreground_color": "#FF5733",
                "background_color": "#00FF00",
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_custom_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "500"},
        )
        assert response.status_code == 200
        img = Image.open(io.BytesIO(response.content))
        assert abs(img.width - 500) < 50

    async def test_content_disposition_header(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
        )
        assert response.headers["content-disposition"] == "inline; filename=qrcode.png"

    async def test_svg_content_disposition(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "svg"},
        )
        assert response.headers["content-disposition"] == "inline; filename=qrcode.svg"


class TestGenerateQRCodeWithLogo:
    def _make_logo_png(self, size: int = 20) -> bytes:
        img = Image.new("RGBA", (size, size), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def test_logo_upload_returns_png(self, client: AsyncClient) -> None:
        logo = self._make_logo_png()
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "https://example.com"},
            files={"logo": ("logo.png", logo, "image/png")},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_logo_with_svg_returns_422(self, client: AsyncClient) -> None:
        logo = self._make_logo_png()
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "svg"},
            files={"logo": ("logo.png", logo, "image/png")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_SVG_CONFLICT"

    async def test_logo_too_large(self, client: AsyncClient) -> None:
        oversized = b"\x00" * 512_001
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.png", oversized, "image/png")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_TOO_LARGE"

    async def test_logo_bad_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.gif", b"GIF89a", "image/gif")},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "LOGO_FORMAT_UNSUPPORTED"

    async def test_logo_jpeg_accepted(self, client: AsyncClient) -> None:
        img = Image.new("RGB", (20, 20), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test"},
            files={"logo": ("logo.jpg", buf.getvalue(), "image/jpeg")},
        )
        assert response.status_code == 200


class TestGenerateQRCodeValidation:
    async def test_missing_data(self, client: AsyncClient) -> None:
        response = await client.post("/v1/generate/qrcode", data={})
        assert response.status_code == 422

    async def test_invalid_format(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "format": "pdf"},
        )
        assert response.status_code == 422

    async def test_invalid_color(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "foreground_color": "notacolor"},
        )
        assert response.status_code == 422
        assert response.json()["error"] == "INVALID_COLOR"

    async def test_size_below_min(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "10"},
        )
        assert response.status_code == 422

    async def test_size_above_max(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "3000"},
        )
        assert response.status_code == 422

    async def test_border_above_max(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "border": "11"},
        )
        assert response.status_code == 422

    async def test_min_boundary_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "50"},
        )
        assert response.status_code == 200

    async def test_max_boundary_size(self, client: AsyncClient) -> None:
        response = await client.post(
            "/v1/generate/qrcode",
            data={"data": "test", "size": "2000"},
        )
        assert response.status_code == 200
