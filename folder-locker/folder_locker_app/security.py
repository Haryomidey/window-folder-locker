"""Password hashing and verification."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import secrets

from .config import PASSWORD_SCHEME, PBKDF2_ITERATIONS, SALT_BYTES
from .errors import LockerError
from .models import PasswordRecord


class PasswordHasher:
    """Create and verify password hashes without storing plaintext passwords."""

    @staticmethod
    def create(password: str) -> PasswordRecord:
        salt = secrets.token_bytes(SALT_BYTES)
        derived = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS,
        )
        return PasswordRecord(
            scheme=PASSWORD_SCHEME,
            iterations=PBKDF2_ITERATIONS,
            salt=base64.b64encode(salt).decode("ascii"),
            hash_value=base64.b64encode(derived).decode("ascii"),
        )

    @staticmethod
    def verify(password: str, record: PasswordRecord) -> bool:
        if record.scheme != PASSWORD_SCHEME:
            raise LockerError(f"Unsupported password scheme: {record.scheme}")

        try:
            salt = base64.b64decode(record.salt.encode("ascii"), validate=True)
            expected = base64.b64decode(
                record.hash_value.encode("ascii"),
                validate=True,
            )
        except (binascii.Error, ValueError, TypeError) as exc:
            raise LockerError("Stored password hash is invalid.") from exc

        actual = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            record.iterations,
        )
        return hmac.compare_digest(actual, expected)
