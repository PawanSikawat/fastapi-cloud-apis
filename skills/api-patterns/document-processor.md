# Document Processor Pattern

## When to Consult
When building an API that accepts a document (PDF, image, spreadsheet) and extracts or transforms its content. Examples: PDF to text, image compression, CSV to JSON, format conversion.

## Principles

1. **File in, result out.** Accept a file upload, process it, return the result. Simple contract.
2. **Support both file upload and URL input.** Some users have files locally; others have them at a URL. Support both.
3. **Stream large outputs.** If the result is a large file (e.g., compressed image, generated PDF), use `StreamingResponse` to avoid holding the full result in memory.
4. **Validate file type and size before processing.** Check MIME type and magic bytes, not just the file extension. Reject early and fast.
5. **Temporary file cleanup is mandatory.** Use `tempfile` with context managers. Never leave temp files on disk after the request completes.

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── convert.py         # or extract.py, compress.py
│   ├── schemas/
│   │   ├── request.py         # Input options (format, quality, pages)
│   │   └── response.py        # Result metadata
│   ├── services/
│   │   ├── processor.py       # Core processing logic
│   │   └── file_handler.py    # File validation, temp file management
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Dual Input (file upload + URL)

```python
from fastapi import File, UploadFile

@router.post("/convert")
async def convert(
    file: UploadFile | None = File(None),
    url: str | None = None,
) -> StreamingResponse:
    if file and url:
        raise AppException(400, "Provide file or URL, not both", "invalid_input")
    if not file and not url:
        raise AppException(400, "Provide file or URL", "missing_input")

    if url:
        content = await fetch_url(url)
    else:
        content = await file.read()

    result = await processor.convert(content)
    return StreamingResponse(result, media_type="application/pdf")
```

### File Validation

```python
import magic

ALLOWED_TYPES = {"application/pdf", "image/png", "image/jpeg"}

def validate_file(content: bytes, max_size: int) -> str:
    if len(content) > max_size:
        raise AppException(413, "File too large", "file_too_large")
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in ALLOWED_TYPES:
        raise AppException(415, f"Unsupported file type: {mime_type}", "unsupported_type")
    return mime_type
```

### Temp File Context Manager

```python
import tempfile
from pathlib import Path

async def process_with_tempfile(content: bytes) -> bytes:
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=True) as tmp:
        tmp.write(content)
        tmp.flush()
        result = await do_processing(Path(tmp.name))
        return result
```

## Anti-Patterns

- **Trusting file extensions.** A `.pdf` extension doesn't mean it's a PDF. Validate with magic bytes.
- **Holding entire output in memory.** A 100-page PDF-to-image conversion can generate gigabytes. Stream the output.
- **No file size limits.** Without limits, a single request can exhaust server memory.
- **Leaving temp files on disk.** Use `tempfile` with `delete=True` or explicit cleanup in a `finally` block.

## Checklist

- [ ] Both file upload and URL input supported
- [ ] File type validated via magic bytes, not extension
- [ ] File size limit enforced before processing
- [ ] Large outputs use StreamingResponse
- [ ] Temp files cleaned up after request completes
- [ ] Processing runs in thread pool if CPU-bound
