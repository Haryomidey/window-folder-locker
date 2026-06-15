"""Expected application errors shown cleanly to users."""


class LockerError(Exception):
    """Base exception for expected folder locker errors."""


class FolderNotFoundError(LockerError):
    """Raised when a requested folder is not available."""


class PasswordError(LockerError):
    """Raised when password verification fails."""


class FolderStateError(LockerError):
    """Raised when a lock or unlock action is invalid for current state."""


class PermissionDeniedError(LockerError):
    """Raised when Windows denies access to attributes or app metadata."""