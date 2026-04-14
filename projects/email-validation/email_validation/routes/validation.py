from typing import Annotated

from fastapi import APIRouter, Depends

from email_validation.config import Settings, get_settings
from email_validation.exceptions import ValidationLimitExceededError
from email_validation.schemas.validation import (
    BatchEmailValidationRequest,
    BatchEmailValidationResponse,
    EmailValidationRequest,
    EmailValidationResponse,
)
from email_validation.services.validator import validate_email, validate_emails

router = APIRouter(prefix="/v1/validate", tags=["validation"])

SettingsDep = Annotated[Settings, Depends(get_settings)]


@router.post("/email", response_model=EmailValidationResponse)
async def validate_single_email(
    body: EmailValidationRequest,
    settings: SettingsDep,
) -> EmailValidationResponse:
    """Validate a single email address with full checks."""
    return await validate_email(body.email, settings)


@router.post("/email/batch", response_model=BatchEmailValidationResponse)
async def validate_batch_emails(
    body: BatchEmailValidationRequest,
    settings: SettingsDep,
) -> BatchEmailValidationResponse:
    """Validate multiple email addresses concurrently."""
    if len(body.emails) > settings.max_batch_size:
        raise ValidationLimitExceededError(settings.max_batch_size)

    results = await validate_emails([str(e) for e in body.emails], settings)
    return BatchEmailValidationResponse(results=results)
