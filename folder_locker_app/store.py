"""Persistent metadata storage for protected folders."""

from __future__ import annotations

import json
from pathlib import Path

from .errors import LockerError, PermissionDeniedError
from .models import ProtectedFolder


class LockerStore:
    """Read and write protected-folder metadata atomically."""

    def __init__(self, config_path: Path) -> None:
        self.config_path = config_path

    def load(self) -> dict[str, ProtectedFolder]:
        if not self.config_path.exists():
            return {}

        try:
            with self.config_path.open("r", encoding="utf-8") as file:
                raw_data = json.load(file)
        except PermissionError as exc:
            raise PermissionDeniedError("Unable to read locker configuration.") from exc
        except json.JSONDecodeError as exc:
            raise LockerError("Locker configuration file is not valid JSON.") from exc

        folders = raw_data.get("folders", {})
        if not isinstance(folders, dict):
            raise LockerError("Locker configuration has an invalid structure.")

        return {
            folder_id: ProtectedFolder.from_dict(folder_data)
            for folder_id, folder_data in folders.items()
        }

    def save(self, folders: dict[str, ProtectedFolder]) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "folders": {
                folder_id: folder.to_dict()
                for folder_id, folder in sorted(folders.items())
            },
        }

        temp_path = self.config_path.with_suffix(".tmp")
        try:
            with temp_path.open("w", encoding="utf-8") as file:
                json.dump(payload, file, indent=2)
                file.write("\n")
            temp_path.replace(self.config_path)
        except PermissionError as exc:
            raise PermissionDeniedError("Unable to write locker configuration.") from exc