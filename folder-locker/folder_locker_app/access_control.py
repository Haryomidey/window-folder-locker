"""Windows access-control operations for locked folders."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from .errors import LockerError, PermissionDeniedError


class WindowsAccessControl:
    """Add and remove a focused read/list deny rule for the current user."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise LockerError("Access control is supported only on Windows.")
        self.principal = self._current_principal()

    def restrict(self, path: Path) -> None:
        """Prevent the current user from opening/listing a locked folder."""

        if self.is_restricted(path):
            return
        self._run_icacls(
            path,
            "/deny",
            f"{self.principal}:(OI)(CI)(RX)",
            error_message="Unable to restrict folder access.",
        )

    def allow(self, path: Path) -> None:
        """Remove deny rules for the current user."""

        if not self.is_restricted(path):
            return
        self._run_icacls(
            path,
            "/remove:d",
            self.principal,
            error_message="Unable to restore folder access.",
        )

    def is_restricted(self, path: Path) -> bool:
        """Return whether this app's current-user deny rule is present."""

        result = self._run_icacls(
            path,
            error_message="Unable to inspect folder permissions.",
            check=False,
        )
        if result.returncode != 0:
            return False

        output = result.stdout.lower()
        return self.principal.lower() in output and "(deny)" in output

    @staticmethod
    def _current_principal() -> str:
        result = subprocess.run(
            ["whoami"],
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode != 0:
            raise LockerError("Unable to identify the current Windows user.")
        return result.stdout.strip()

    @staticmethod
    def _run_icacls(
        path: Path,
        *args: str,
        error_message: str,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            ["icacls", str(path), *args],
            capture_output=True,
            check=False,
            text=True,
        )
        if check and result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip()
            if "access is denied" in message.lower():
                raise PermissionDeniedError(error_message)
            raise LockerError(f"{error_message} {message}".strip())
        return result
