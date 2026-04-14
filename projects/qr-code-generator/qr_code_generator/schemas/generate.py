import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class QRCodeRequest(BaseModel):
    data: str = Field(min_length=1, max_length=2953)
    format: Literal["png", "svg"] = "png"
    size: int = Field(default=300, ge=50, le=2000)
    error_correction: Literal["L", "M", "Q", "H"] = "M"
    border: int = Field(default=4, ge=0, le=10)
    foreground_color: str = Field(default="#000000")
    background_color: str = Field(default="#ffffff")
    logo_size_ratio: float = Field(default=0.25, ge=0.1, le=0.4)

    @field_validator("foreground_color", "background_color")
    @classmethod
    def validate_hex_color(cls, v: str) -> str:
        if not _HEX_COLOR_RE.match(v):
            msg = f"Invalid hex color: {v!r} — expected format #RRGGBB"
            raise ValueError(msg)
        return v.lower()
