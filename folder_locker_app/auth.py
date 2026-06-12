"""App-level password gate for the desktop GUI."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import LockerError, PasswordError, PermissionDeniedError
from .models import PasswordRecord
from .security import PasswordHasher


class AppAuthenticator:
    """Persist and verify the password required to open the GUI."""

    def __init__(self, auth_path: Path) -> None:
        self.auth_path = auth_path

    def is_configured(self) -> bool:
        return self.auth_path.exists()

    def set_password(self, password: str) -> None:
        self._validate_password(password)
        self.auth_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "password": PasswordHasher.create(password).to_dict(),
        }
        temp_path = self.auth_path.with_suffix(".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2)
                file.write("\n")
            temp_path.replace(self.auth_path)
        except PermissionError as exc:
            raise PermissionDeniedError("Unable to save app password.") from exc

    def verify(self, password: str) -> None:
        record = self._load_password()
        if not PasswordHasher.verify(password, record):
            raise PasswordError("Incorrect app password.")

    def _load_password(self) -> PasswordRecord:
        if not self.auth_path.exists():
            raise PasswordError("App password has not been created yet.")

        try:
            with self.auth_path.open("r", encoding="utf-8") as file:
                payload = json.load(file)
        except PermissionError as exc:
            raise PermissionDeniedError("Unable to read app password.") from exc
        except json.JSONDecodeError as exc:
            raise LockerError("App password file is not valid JSON.") from exc

        try:
            password_data = payload["password"]
        except (KeyError, TypeError) as exc:
            raise LockerError("App password file has an invalid structure.") from exc

        return PasswordRecord.from_dict(password_data)

    @staticmethod
    def _validate_password(password: str) -> None:
        if not password:
            raise PasswordError("Password cannot be empty.")
        if len(password) < 8:
            raise PasswordError("Password must be at least 8 characters.")
