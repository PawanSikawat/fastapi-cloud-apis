import re

# RFC 5321 local-part max 64 chars, domain max 255 chars, total max 254 chars
_MAX_EMAIL_LENGTH = 254
_MAX_LOCAL_LENGTH = 64
_MAX_DOMAIN_LENGTH = 255

# Simplified RFC 5322 pattern — catches the vast majority of invalid addresses
# without being overly permissive
_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


def check_syntax(email: str) -> tuple[bool, str | None]:
    """Validate email syntax. Returns (valid, reason_if_invalid)."""
    if not email or len(email) > _MAX_EMAIL_LENGTH:
        return False, f"Email exceeds maximum length of {_MAX_EMAIL_LENGTH} characters"

    if "@" not in email:
        return False, "Missing @ symbol"

    local, _, domain = email.rpartition("@")

    if not local:
        return False, "Empty local part"

    if len(local) > _MAX_LOCAL_LENGTH:
        return False, f"Local part exceeds maximum length of {_MAX_LOCAL_LENGTH} characters"

    if not domain:
        return False, "Empty domain"

    if len(domain) > _MAX_DOMAIN_LENGTH:
        return False, f"Domain exceeds maximum length of {_MAX_DOMAIN_LENGTH} characters"

    if ".." in email:
        return False, "Consecutive dots not allowed"

    if local.startswith(".") or local.endswith("."):
        return False, "Local part cannot start or end with a dot"

    if "." not in domain:
        return False, "Domain must contain at least one dot"

    tld = domain.rsplit(".", 1)[-1]
    if len(tld) < 2:
        return False, "Top-level domain must be at least 2 characters"

    if not _EMAIL_REGEX.match(email):
        return False, "Invalid characters in email address"

    return True, None
