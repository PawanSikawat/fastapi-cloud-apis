import pytest
from pydantic import ValidationError


class TestQRCodeRequestDefaults:
    def test_minimal_request(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="hello")
        assert req.data == "hello"
        assert req.format == "png"
        assert req.size == 300
        assert req.error_correction == "M"
        assert req.border == 4
        assert req.foreground_color == "#000000"
        assert req.background_color == "#ffffff"
        assert req.logo_size_ratio == 0.25


class TestQRCodeRequestColorValidation:
    def test_valid_hex_colors(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(
            data="test",
            foreground_color="#FF5733",
            background_color="#00aaFF",
        )
        assert req.foreground_color == "#ff5733"
        assert req.background_color == "#00aaff"

    def test_invalid_foreground_color(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="foreground_color"):
            QRCodeRequest(data="test", foreground_color="notacolor")

    def test_invalid_background_color_short(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="background_color"):
            QRCodeRequest(data="test", background_color="#FFF")

    def test_color_without_hash(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="foreground_color"):
            QRCodeRequest(data="test", foreground_color="000000")


class TestQRCodeRequestBoundaries:
    def test_size_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", size=50)
        assert req.size == 50

    def test_size_below_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="size"):
            QRCodeRequest(data="test", size=49)

    def test_size_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", size=2000)
        assert req.size == 2000

    def test_size_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="size"):
            QRCodeRequest(data="test", size=2001)

    def test_border_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", border=0)
        assert req.border == 0

    def test_border_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="border"):
            QRCodeRequest(data="test", border=11)

    def test_logo_size_ratio_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", logo_size_ratio=0.1)
        assert req.logo_size_ratio == 0.1

    def test_logo_size_ratio_below_min(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="logo_size_ratio"):
            QRCodeRequest(data="test", logo_size_ratio=0.05)

    def test_logo_size_ratio_above_max(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="logo_size_ratio"):
            QRCodeRequest(data="test", logo_size_ratio=0.5)

    def test_empty_data(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="data"):
            QRCodeRequest(data="")


class TestQRCodeRequestFormat:
    def test_png_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", format="png")
        assert req.format == "png"

    def test_svg_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", format="svg")
        assert req.format == "svg"

    def test_invalid_format(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="format"):
            QRCodeRequest(data="test", format="pdf")


class TestQRCodeRequestErrorCorrection:
    @pytest.mark.parametrize("level", ["L", "M", "Q", "H"])
    def test_valid_levels(self, level: str) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        req = QRCodeRequest(data="test", error_correction=level)
        assert req.error_correction == level

    def test_invalid_level(self) -> None:
        from qr_code_generator.schemas.generate import QRCodeRequest

        with pytest.raises(ValidationError, match="error_correction"):
            QRCodeRequest(data="test", error_correction="X")
