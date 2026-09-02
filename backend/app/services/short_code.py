"""Short-code generation strategy — see docs/adr/ADR-002-short-code-strategy.md
for the alternatives considered (random Base62 / sequential Base62 /
UUID-based) and why random Base62 with DB-enforced collision retry was
chosen."""

import secrets
import string

ALPHABET = string.digits + string.ascii_uppercase + string.ascii_lowercase  # Base62
DEFAULT_LENGTH = 7


def generate_short_code(length: int = DEFAULT_LENGTH) -> str:
    # secrets.choice (CSPRNG), not random.choice: a short code gates access
    # to whatever URL it points to, and a predictable PRNG would make codes
    # guessable/enumerable.
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
