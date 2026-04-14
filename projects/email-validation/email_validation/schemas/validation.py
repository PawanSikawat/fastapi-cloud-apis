from pydantic import BaseModel, EmailStr


class EmailValidationRequest(BaseModel):
    email: EmailStr


class BatchEmailValidationRequest(BaseModel):
    emails: list[EmailStr]


class SyntaxCheck(BaseModel):
    valid: bool
    reason: str | None = None


class MxCheck(BaseModel):
    valid: bool
    records: list[str] = []


class SmtpCheck(BaseModel):
    verified: bool | None = None
    catch_all: bool | None = None
    reason: str | None = None


class ValidationChecks(BaseModel):
    syntax: SyntaxCheck
    mx: MxCheck
    smtp: SmtpCheck


class EmailValidationResponse(BaseModel):
    email: str
    result: str
    score: float
    is_deliverable: bool | None
    is_disposable: bool
    is_role_based: bool
    is_free_provider: bool
    checks: ValidationChecks


class BatchEmailValidationResponse(BaseModel):
    results: list[EmailValidationResponse]
