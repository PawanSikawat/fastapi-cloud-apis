import hashlib
import secrets


def generate_api_key(prefix: str = "sk") -> tuple[str, str, str]:
    """Generate an API key. Returns (full_key, key_prefix, key_hash)."""
    random_part = secrets.token_urlsafe(32)
    full_key = f"{prefix}_{random_part}"
    key_prefix = full_key[:12]
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    return full_key, key_prefix, key_hash


def hash_api_key(key: str) -> str:
    """Hash an API key for storage/lookup."""
    return hashlib.sha256(key.encode()).hexdigest()
