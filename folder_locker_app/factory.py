"""Application object factory."""

from __future__ import annotations

from pathlib import Path

from .access_control import WindowsAccessControl
from .config import CONFIG_FILE
from .logging_setup import setup_logging
from .service import FolderLocker
from .store import LockerStore
from .windows_attributes import WindowsAttributes


def create_locker(data_dir: Path) -> FolderLocker:
    """Create a configured locker service."""

    setup_logging(data_dir)
    store = LockerStore(data_dir / CONFIG_FILE)
    return FolderLocker(store, WindowsAttributes(), WindowsAccessControl())
