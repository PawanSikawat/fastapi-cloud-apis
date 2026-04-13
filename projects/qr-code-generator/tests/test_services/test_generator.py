import io

from PIL import Image


class TestGenerateQR:
    def test_png_output_is_valid_png(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com")
        result = generate_qr(params)

        assert result[:8] == b"\x89PNG\r\n\x1a\n"
        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_svg_output_contains_svg_tag(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com", format="svg")
        result = generate_qr(params)

        svg_text = result.decode("utf-8")
        assert "<svg" in svg_text
        assert "</svg>" in svg_text

    def test_custom_colors(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(
            data="test",
            foreground_color="#ff0000",
            background_color="#00ff00",
        )
        result = generate_qr(params)

        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_size_approximates_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="test", size=500)
        result = generate_qr(params)

        img = Image.open(io.BytesIO(result))
        assert abs(img.width - 500) < 50

    def test_border_zero(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params_no_border = QRCodeRequest(data="test", border=0)
        params_with_border = QRCodeRequest(data="test", border=4)

        img_no = Image.open(io.BytesIO(generate_qr(params_no_border)))
        img_with = Image.open(io.BytesIO(generate_qr(params_with_border)))
        assert img_no.width < img_with.width

    def test_data_overflow_raises_invalid_data(self) -> None:
        import pytest

        from qr_code_generator.exceptions import InvalidDataError
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="x" * 2953, error_correction="H")
        with pytest.raises(InvalidDataError):
            generate_qr(params)


class TestLogoCompositing:
    def _make_logo(self, width: int = 20, height: int = 20) -> bytes:
        img = Image.new("RGBA", (width, height), (255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    def test_logo_produces_valid_png(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com")
        logo_bytes = self._make_logo()
        result = generate_qr(params, logo_bytes=logo_bytes)

        img = Image.open(io.BytesIO(result))
        assert img.format == "PNG"

    def test_logo_changes_center_pixels(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="https://example.com", size=300)
        result_no_logo = generate_qr(params)
        result_with_logo = generate_qr(params, logo_bytes=self._make_logo())

        img_no = Image.open(io.BytesIO(result_no_logo)).convert("RGBA")
        img_with = Image.open(io.BytesIO(result_with_logo)).convert("RGBA")
        cx, cy = img_no.width // 2, img_no.height // 2
        assert img_no.getpixel((cx, cy)) != img_with.getpixel((cx, cy))

    def test_error_correction_elevated_to_h_with_logo(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params_l = QRCodeRequest(data="test", error_correction="L")
        params_h = QRCodeRequest(data="test", error_correction="H")

        result_l_logo = generate_qr(params_l, logo_bytes=self._make_logo())
        result_h_no_logo = generate_qr(params_h)

        img_l = Image.open(io.BytesIO(result_l_logo))
        img_h = Image.open(io.BytesIO(result_h_no_logo))
        assert img_l.width == img_h.width

    def test_logo_with_jpeg(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        img = Image.new("RGB", (20, 20), (255, 0, 0))
        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()

        params = QRCodeRequest(data="test")
        result = generate_qr(params, logo_bytes=jpeg_bytes)
        assert result[:8] == b"\x89PNG\r\n\x1a\n"


class TestScaleCalculation:
    def test_small_data_small_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="A", size=50, border=0)
        result = generate_qr(params)
        img = Image.open(io.BytesIO(result))
        assert img.width >= 21

    def test_large_target(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest
        from qr_code_generator.services.generator import generate_qr

        params = QRCodeRequest(data="A", size=2000, border=0)
        result = generate_qr(params)
        img = Image.open(io.BytesIO(result))
        assert img.width <= 2000
        assert img.width > 1900
