"""Windows hidden file attribute operations."""

from __future__ import annotations

import ctypes
import os
from ctypes import wintypes
from pathlib import Path

from .config import (
    FILE_ATTRIBUTE_HIDDEN,
    FILE_ATTRIBUTE_SYSTEM,
    INVALID_FILE_ATTRIBUTES,
)
from .errors import LockerError, PermissionDeniedError


class WindowsAttributes:
    """Small wrapper around Windows file attribute APIs."""

    def __init__(self) -> None:
        if os.name != "nt":
            raise LockerError("This application is supported only on Windows.")

        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.GetFileAttributesW.argtypes = [wintypes.LPCWSTR]
        self._kernel32.GetFileAttributesW.restype = wintypes.DWORD
        self._kernel32.SetFileAttributesW.argtypes = [
            wintypes.LPCWSTR,
            wintypes.DWORD,
        ]
        self._kernel32.SetFileAttributesW.restype = wintypes.BOOL

    def is_hidden(self, path: Path) -> bool:
        attributes = self._get_attributes(path)
        return bool(attributes & FILE_ATTRIBUTE_HIDDEN)

    def is_locked(self, path: Path) -> bool:
        attributes = self._get_attributes(path)
        protected_attributes = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
        return (attributes & protected_attributes) == protected_attributes

    def hide(self, path: Path) -> None:
        attributes = self._get_attributes(path)
        locked_attributes = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
        self._set_attributes(path, attributes | locked_attributes)

    def unhide(self, path: Path) -> None:
        attributes = self._get_attributes(path)
        locked_attributes = FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
        self._set_attributes(path, attributes & ~locked_attributes)

    def _get_attributes(self, path: Path) -> int:
        result = self._kernel32.GetFileAttributesW(str(path))
        if result == INVALID_FILE_ATTRIBUTES:
            self._raise_last_windows_error("Unable to read folder attributes.")
        return int(result)

    def _set_attributes(self, path: Path, attributes: int) -> None:
        result = self._kernel32.SetFileAttributesW(str(path), attributes)
        if result == 0:
            self._raise_last_windows_error("Unable to update folder attributes.")

    @staticmethod
    def _raise_last_windows_error(message: str) -> None:
        error_code = ctypes.get_last_error()
        exc = ctypes.WinError(error_code)
        if getattr(exc, "winerror", None) == 5:
            raise PermissionDeniedError(message) from exc
        raise LockerError(f"{message} Windows error {error_code}.") from exc
