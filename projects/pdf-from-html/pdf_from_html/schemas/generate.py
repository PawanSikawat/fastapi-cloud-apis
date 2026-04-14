from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Margin(BaseModel):
    top: str = "20mm"
    right: str = "20mm"
    bottom: str = "20mm"
    left: str = "20mm"


class PDFOptions(BaseModel):
    format: Literal["A4", "Letter", "Legal", "Tabloid"] = "A4"
    orientation: Literal["portrait", "landscape"] = "portrait"
    margin: Margin = Field(default_factory=Margin)
    scale: float = 1.0
    print_background: bool = True
    page_ranges: str | None = None
    header_html: str | None = None
    footer_html: str | None = None
    width: str | None = None
    height: str | None = None

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: float) -> float:
        if not 0.1 <= v <= 2.0:
            msg = "Scale must be between 0.1 and 2.0"
            raise ValueError(msg)
        return v


class PDFGenerateRequest(BaseModel):
    source: Literal["raw", "url"]
    content: str = Field(min_length=1)
    options: PDFOptions = Field(default_factory=PDFOptions)
