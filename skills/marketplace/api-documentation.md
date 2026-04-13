# API Documentation Standards

## When to Consult
When writing endpoint documentation, creating examples, or improving the developer experience of an API.

## Principles

1. **FastAPI generates the docs.** Use docstrings, `summary`, `description`, `response_model`, and `responses` parameters on route decorators. The OpenAPI spec is the single source of truth.
2. **Every endpoint needs at least 3 examples.** A minimal request, a fully-specified request, and an error case. Use FastAPI's `openapi_examples` parameter.
3. **Error responses must be documented.** Use the `responses` parameter to document all possible error status codes with example response bodies.
4. **Schema descriptions on every field.** Use Pydantic `Field(description="...")` on every field. These appear in the auto-generated docs.

## Patterns

### Route with Full Documentation

```python
@router.post(
    "/validate",
    summary="Validate an email address",
    description="Checks syntax, MX records, SMTP reachability, and disposable email detection.",
    response_model=ValidationResponse,
    responses={
        400: {"description": "Invalid email format", "model": ErrorResponse},
        429: {"description": "Rate limit or quota exceeded", "model": ErrorResponse},
    },
)
async def validate_email(request: ValidationRequest) -> ValidationResponse:
    ...
```

### Pydantic Schema with Descriptions

```python
class ValidationRequest(BaseModel):
    email: str = Field(
        description="Email address to validate",
        examples=["user@example.com"],
    )
    check_smtp: bool = Field(
        default=True,
        description="Whether to verify the mailbox exists via SMTP",
    )

class ValidationResponse(BaseModel):
    email: str = Field(description="The email address that was validated")
    is_valid: bool = Field(description="Overall validation result")
    checks: CheckResults = Field(description="Detailed results for each check")
```

### OpenAPI Examples

```python
@router.post(
    "/validate",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "examples": {
                        "minimal": {
                            "summary": "Minimal request",
                            "value": {"email": "user@example.com"},
                        },
                        "full": {
                            "summary": "Full request with options",
                            "value": {"email": "user@example.com", "check_smtp": True},
                        },
                    }
                }
            }
        }
    },
)
```

## Anti-Patterns

- **No descriptions on schema fields.** `email: str` tells the developer nothing about format expectations. Add `Field(description=...)`.
- **Only documenting happy path.** Error responses are more important than success responses — developers need to know what can go wrong.
- **Writing docs in a separate file.** Docs belong in the code (docstrings, Field descriptions, route parameters). Separate docs get out of sync.
- **Using generic examples.** `"string"`, `"example@example.com"` — use realistic data like `"alice.smith@company.com"`.

## Checklist

- [ ] Every route has `summary` and `description`
- [ ] Every Pydantic field has `description` and `examples`
- [ ] Error responses documented with `responses` parameter
- [ ] At least 3 OpenAPI examples per endpoint
- [ ] `/docs` (Swagger UI) loads and all endpoints are testable
- [ ] Error response includes `error` code and `detail` message
