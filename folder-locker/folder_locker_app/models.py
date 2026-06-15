"""Serializable data models for protected folders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import LockerError


@dataclass(frozen=True)
class PasswordRecord:
    """Stored password verification data."""

    scheme: str
    iterations: int
    salt: str
    hash_value: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme": self.scheme,
            "iterations": self.iterations,
            "salt": self.salt,
            "hash": self.hash_value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PasswordRecord":
        try:
            return cls(
                scheme=str(data["scheme"]),
                iterations=int(data["iterations"]),
                salt=str(data["salt"]),
                hash_value=str(data["hash"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise LockerError("Stored password metadata is invalid.") from exc


@dataclass(frozen=True)
class ProtectedFolder:
    """Configuration for one protected folder."""

    folder_id: str
    path: Path
    password: PasswordRecord

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.folder_id,
            "path": str(self.path),
            "password": self.password.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProtectedFolder":
        try:
            return cls(
                folder_id=str(data["id"]),
                path=Path(str(data["path"])),
                password=PasswordRecord.from_dict(data["password"]),
            )
        except (KeyError, TypeError) as exc:
            raise LockerError("Stored folder metadata is invalid.") from exc


@dataclass(frozen=True)
class FolderView:
    """Folder data prepared for the CLI and GUI."""

    folder_id: str
    path: Path
    exists: bool
    is_locked: bool

    @property
    def status(self) -> str:
        if not self.exists:
            return "Missing"
        if self.is_locked:
            return "Locked"
        return "Unlocked"