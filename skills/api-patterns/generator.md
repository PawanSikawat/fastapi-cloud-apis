# Generator Pattern

## When to Consult
When building an API that creates artifacts from parameters. Examples: QR codes, barcodes, PDFs, invoices, placeholder images, screenshots.

## Principles

1. **Input is parameters, output is a file.** The consumer sends JSON options (text, colors, size), the API returns an image/PDF/file.
2. **Support multiple output formats.** QR code API should support PNG, SVG, and PDF. Let the consumer choose via query parameter or Accept header.
3. **Sensible defaults for everything.** A QR code request with just `data=hello` should return a usable image. Colors, size, format should all have defaults.
4. **Cache generated artifacts.** The same parameters produce the same output. Cache by hashing the input parameters. Saves CPU for repeat requests.
5. **Return the file directly, not a URL.** For small artifacts (QR codes, barcodes), return the binary data with the correct Content-Type. No extra round-trip.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── <package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── generate.py        # Accepts parameters, returns artifact
│   ├── schemas/
│   │   └── request.py         # Generation options with defaults
│   ├── services/
│   │   └── generator.py       # Core generation logic
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Request Schema with Defaults

```python
class GenerateRequest(BaseModel):
    data: str                              # Required
    format: Literal["png", "svg", "pdf"] = "png"
    size: int = Field(default=300, ge=50, le=2000)
    foreground_color: str = "#000000"
    background_color: str = "#FFFFFF"
```

### Binary Response

```python
@router.post("/generate", response_class=Response)
async def generate(params: GenerateRequest) -> Response:
    content = await generator.create(params)
    media_types = {"png": "image/png", "svg": "image/svg+xml", "pdf": "application/pdf"}
    return Response(
        content=content,
        media_type=media_types[params.format],
        headers={"Content-Disposition": f"inline; filename=output.{params.format}"},
    )
```

### Input-Based Caching

```python
import hashlib
import json

def cache_key(params: GenerateRequest) -> str:
    param_str = json.dumps(params.model_dump(), sort_keys=True)
    return f"gen:{hashlib.sha256(param_str.encode()).hexdigest()}"
```

## Anti-Patterns

- **Returning a URL instead of the file.** For artifacts under 1MB, return the binary directly. URLs add latency and require storage management.
- **No format options.** SVG is better for web, PNG for apps, PDF for print. Support all three when feasible.
- **Ignoring Content-Disposition header.** Without it, browsers don't know the filename. Use `inline` for display, `attachment` for download.
- **No input validation on size/dimensions.** A 50,000x50,000 pixel image request will OOM the server. Set max dimensions.

## Checklist

- [ ] Multiple output formats supported
- [ ] Sensible defaults for all optional parameters
- [ ] Input validation with min/max bounds on dimensions
- [ ] Binary response with correct Content-Type
- [ ] Content-Disposition header set
- [ ] Repeat requests cached by input hash
- [ ] Max output size enforced
