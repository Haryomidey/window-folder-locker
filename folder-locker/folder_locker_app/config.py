"""Application constants and filesystem locations."""

from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "FolderLocker"
CONFIG_FILE = "folders.json"
AUTH_FILE = "app-auth.json"
LOG_FILE = "locker.log"
PASSWORD_SCHEME = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 600_000
SALT_BYTES = 32
FILE_ATTRIBUTE_HIDDEN = 0x02
FILE_ATTRIBUTE_SYSTEM = 0x04
INVALID_FILE_ATTRIBUTES = 0xFFFFFFFF


def default_data_dir() -> Path:
    """Return a per-user app data directory for configuration and logs."""

    app_data = os.environ.get("APPDATA")
    if app_data:
        return Path(app_data) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"
