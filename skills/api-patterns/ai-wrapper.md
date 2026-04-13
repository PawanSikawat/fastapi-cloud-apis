# AI Wrapper Pattern

## When to Consult
When building an API that wraps a machine learning model or external AI service. Examples: OCR, background removal, sentiment analysis, summarization, translation.

## Principles

1. **Pick the right model tier.** Open-source models (Tesseract, rembg, VADER) for cost-sensitive APIs. External AI APIs (OpenAI, Claude) for quality-sensitive APIs. Never use an expensive model where a cheap one suffices.
2. **Async processing for heavy inference.** If inference takes > 2 seconds, return a job ID and let the client poll or use a webhook callback.
3. **Input size limits are non-negotiable.** Unbounded input (a 500MB image, a 100-page PDF) will crash your server or blow your costs. Set limits per plan.
4. **Model versioning matters.** When you upgrade a model, old responses may differ. Version your model in the response metadata so users know what generated the result.
5. **Fallback chain for reliability.** Primary model → fallback model → graceful error. Example: custom OCR model → Tesseract fallback → "unable to extract text."

## Patterns

### Project Structure

```
projects/<name>/
├── pyproject.toml
├── src/<package_name>/
│   ├── main.py
│   ├── config.py
│   ├── routes/
│   │   └── process.py         # Accepts input, returns result
│   ├── schemas/
│   │   ├── request.py         # Input constraints (max size, format)
│   │   └── response.py        # Result + metadata (model version, confidence)
│   ├── services/
│   │   ├── model.py           # Model loading and inference
│   │   └── preprocessor.py    # Input normalization
│   └── exceptions.py
└── tests/
    ├── conftest.py
    ├── test_routes/
    └── test_services/
```

### Response Schema

```python
class AIResponse(BaseModel):
    result: ResultModel
    model_version: str      # e.g., "tesseract-5.3.1" or "rembg-2.0.50"
    confidence: float | None  # 0.0-1.0 if applicable
    processing_time_ms: int
```

### Sync vs Async Decision

```
Inference time < 2s  →  Synchronous response
Inference time 2-30s →  Return job_id, poll endpoint
Inference time > 30s →  Return job_id, webhook callback
```

### File Upload Handling

```python
from fastapi import UploadFile

@router.post("/process")
async def process_file(
    file: UploadFile,
    auth: AuthContext = Depends(require_api_key),
) -> AIResponse:
    if file.size and file.size > settings.max_file_size:
        raise AppException(413, "File too large", "file_too_large")
    content = await file.read()
    result = await model_service.process(content)
    return AIResponse(result=result, ...)
```

## Anti-Patterns

- **Loading the model on every request.** Load once at startup (lifespan), reuse across requests. Model loading takes seconds; inference takes milliseconds.
- **No input size limits.** A 1GB upload will OOM your server. Enforce limits at the route level.
- **Blocking the event loop with CPU-bound inference.** Use `asyncio.to_thread()` or a process pool for CPU-heavy model inference.
- **No confidence scores.** If the model supports it, always return confidence. Users want to filter low-confidence results.

## Checklist

- [ ] Model loaded once at startup, not per request
- [ ] Input size limits enforced per plan
- [ ] CPU-bound inference runs in thread/process pool
- [ ] Response includes model_version and processing_time_ms
- [ ] Confidence score included when model supports it
- [ ] File upload uses FastAPI's UploadFile (streaming, not loading full body into memory)
