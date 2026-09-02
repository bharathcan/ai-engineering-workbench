"""IP hashing for Advanced User Analytics — see ADR-005. The raw IP is
never persisted; only a salted SHA-256 hash, used solely to derive
is_repeat_visitor (same hash seen before for this URL)."""

import hashlib
import secrets

from app.core.config import settings

# Generated once per process if not explicitly configured — see
# app.core.config.Settings.ip_hash_salt for the reasoning.
_RUNTIME_SALT = settings.ip_hash_salt or secrets.token_hex(32)


def hash_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None
    return hashlib.sha256(f"{_RUNTIME_SALT}:{ip_address}".encode()).hexdigest()
