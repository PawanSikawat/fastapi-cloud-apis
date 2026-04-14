import asyncio

from email_validation.config import Settings
from email_validation.schemas.validation import (
    EmailValidationResponse,
    MxCheck,
    SmtpCheck,
    SyntaxCheck,
    ValidationChecks,
)
from email_validation.services.disposable import is_disposable
from email_validation.services.dns_lookup import check_mx
from email_validation.services.free_provider import is_free_provider
from email_validation.services.role_based import is_role_based
from email_validation.services.smtp import verify_smtp
from email_validation.services.syntax import check_syntax


def _compute_score(
    *,
    syntax_valid: bool,
    mx_valid: bool,
    smtp_verified: bool | None,
    smtp_catch_all: bool | None,
    disposable: bool,
    role_based: bool,
) -> float:
    if not syntax_valid or not mx_valid:
        return 0.0

    score = 1.0

    if smtp_verified is False:
        score = 0.1
    elif smtp_verified is None:
        score -= 0.1

    if smtp_catch_all:
        score -= 0.2

    if disposable:
        score -= 0.3

    if role_based:
        score -= 0.1

    return max(0.0, min(1.0, round(score, 2)))


def _determine_result(score: float) -> str:
    if score >= 0.8:
        return "deliverable"
    if score >= 0.5:
        return "risky"
    if score >= 0.1:
        return "unknown"
    return "undeliverable"


def _determine_deliverable(score: float) -> bool | None:
    if score >= 0.8:
        return True
    if score < 0.1:
        return False
    return None


async def validate_email(email: str, settings: Settings) -> EmailValidationResponse:
    """Run all validation checks on a single email address."""
    # Step 1: Syntax check (synchronous, fast)
    syntax_valid, syntax_reason = check_syntax(email)

    if not syntax_valid:
        return EmailValidationResponse(
            email=email,
            result="undeliverable",
            score=0.0,
            is_deliverable=False,
            is_disposable=False,
            is_role_based=False,
            is_free_provider=False,
            checks=ValidationChecks(
                syntax=SyntaxCheck(valid=False, reason=syntax_reason),
                mx=MxCheck(valid=False),
                smtp=SmtpCheck(reason="Skipped — syntax invalid"),
            ),
        )

    domain = email.rsplit("@", 1)[1]

    # Step 2: Run independent checks concurrently
    mx_coro = check_mx(domain, timeout=settings.dns_timeout)
    disposable = is_disposable(domain)
    role_based = is_role_based(email)
    free_provider = is_free_provider(domain)

    mx_valid, mx_records = await mx_coro

    # Step 3: SMTP check (depends on MX results)
    smtp_verified: bool | None = None
    smtp_catch_all: bool | None = None
    smtp_reason: str | None = None

    if mx_valid and settings.smtp_enabled and mx_records:
        smtp_verified, smtp_catch_all, smtp_reason = await verify_smtp(
            email, mx_records[0], timeout=settings.smtp_timeout
        )
    elif not mx_valid:
        smtp_reason = "Skipped — no MX records"
    elif not settings.smtp_enabled:
        smtp_reason = "SMTP verification disabled"

    # Step 4: Score and result
    score = _compute_score(
        syntax_valid=syntax_valid,
        mx_valid=mx_valid,
        smtp_verified=smtp_verified,
        smtp_catch_all=smtp_catch_all,
        disposable=disposable,
        role_based=role_based,
    )

    return EmailValidationResponse(
        email=email,
        result=_determine_result(score),
        score=score,
        is_deliverable=_determine_deliverable(score),
        is_disposable=disposable,
        is_role_based=role_based,
        is_free_provider=free_provider,
        checks=ValidationChecks(
            syntax=SyntaxCheck(valid=True),
            mx=MxCheck(valid=mx_valid, records=mx_records),
            smtp=SmtpCheck(
                verified=smtp_verified,
                catch_all=smtp_catch_all,
                reason=smtp_reason,
            ),
        ),
    )


async def validate_emails(emails: list[str], settings: Settings) -> list[EmailValidationResponse]:
    """Validate multiple emails concurrently."""
    tasks = [validate_email(email, settings) for email in emails]
    return list(await asyncio.gather(*tasks))
