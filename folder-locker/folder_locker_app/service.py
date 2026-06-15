"""Application service for folder locker operations."""

from __future__ import annotations

import hashlib
import logging
import os
from pathlib import Path

from .access_control import WindowsAccessControl
from .errors import (
    FolderNotFoundError,
    FolderStateError,
    LockerError,
    PasswordError,
    PermissionDeniedError,
)
from .models import FolderView, ProtectedFolder
from .security import PasswordHasher
from .store import LockerStore
from .windows_attributes import WindowsAttributes


class FolderLocker:
    """Core locker behavior independent from CLI and GUI layers."""

    def __init__(
        self,
        store: LockerStore,
        attributes: WindowsAttributes,
        access_control: WindowsAccessControl,
    ) -> None:
        self.store = store
        self.attributes = attributes
        self.access_control = access_control

    def create(self, folder_path: Path, password: str) -> ProtectedFolder:
        self._validate_new_password(password)
        folder = self._resolve_existing_folder(folder_path)
        folder_id = self.folder_id(folder)
        folders = self.store.load()

        if folder_id in folders:
            raise LockerError("This folder is already protected.")

        protected = ProtectedFolder(
            folder_id=folder_id,
            path=folder,
            password=PasswordHasher.create(password),
        )
        folders[folder_id] = protected
        self.store.save(folders)
        logging.info("Protected folder created: folder_id=%s", folder_id)
        return protected

    def lock(self, folder_id: str) -> None:
        protected = self.get_folder(folder_id)
        self._ensure_folder_exists(protected.path)

        is_hidden = self.attributes.is_locked(protected.path)
        is_restricted = self.access_control.is_restricted(protected.path)
        if is_hidden and is_restricted:
            raise FolderStateError("Folder is already locked.")

        try:
            if not is_hidden:
                self.attributes.hide(protected.path)
            if not is_restricted:
                self.access_control.restrict(protected.path)
        except LockerError:
            if not is_hidden:
                try:
                    self.attributes.unhide(protected.path)
                except LockerError:
                    logging.exception(
                        "Unable to roll back hidden attributes after failed lock: "
                        "folder_id=%s",
                        protected.folder_id,
                    )
            raise
        logging.info("Folder locked: folder_id=%s", protected.folder_id)

    def unlock(self, folder_id: str, password: str) -> None:
        protected = self.get_folder(folder_id)
        self.verify_password(folder_id, password, "unlock")

        is_restricted = self.access_control.is_restricted(protected.path)
        if is_restricted:
            self.access_control.allow(protected.path)

        is_hidden = self.attributes.is_locked(protected.path)
        if not is_hidden and not is_restricted:
            raise FolderStateError("Folder is already unlocked.")

        self._ensure_folder_exists(protected.path)
        if is_hidden:
            self.attributes.unhide(protected.path)
        logging.info("Folder unlocked: folder_id=%s", protected.folder_id)

    def change_password(
        self,
        folder_id: str,
        current_password: str,
        new_password: str,
    ) -> None:
        self._validate_new_password(new_password)
        protected = self.get_folder(folder_id)
        self.verify_password(folder_id, current_password, "password change")

        folders = self.store.load()
        folders[folder_id] = ProtectedFolder(
            folder_id=folder_id,
            path=protected.path,
            password=PasswordHasher.create(new_password),
        )
        self.store.save(folders)
        logging.info("Password changed: folder_id=%s", folder_id)

    def forget(self, folder_id: str, password: str) -> None:
        self.verify_password(folder_id, password, "forget")
        folders = self.store.load()
        protected = folders.pop(folder_id, None)
        if protected is None:
            raise LockerError("This folder is not protected yet.")
        self.store.save(folders)
        logging.info("Protected folder forgotten: folder_id=%s", folder_id)

    def verify_password(
        self,
        folder_id: str,
        password: str,
        action: str = "verification",
    ) -> None:
        protected = self.get_folder(folder_id)
        if not PasswordHasher.verify(password, protected.password):
            logging.warning(
                "Failed %s attempt: folder_id=%s",
                action,
                protected.folder_id,
            )
            raise PasswordError("Incorrect password.")

    def list_folders(self) -> list[FolderView]:
        views = []
        for protected in self.store.load().values():
            is_restricted = self.access_control.is_restricted(protected.path)
            exists = is_restricted or (
                protected.path.exists() and protected.path.is_dir()
            )
            is_locked = is_restricted
            if exists and not is_locked:
                is_locked = self.attributes.is_locked(protected.path)
            views.append(
                FolderView(
                    folder_id=protected.folder_id,
                    path=protected.path,
                    exists=exists,
                    is_locked=is_locked,
                )
            )
        return sorted(views, key=lambda item: str(item.path).lower())

    def get_folder(self, folder_id: str) -> ProtectedFolder:
        folders = self.store.load()
        try:
            return folders[folder_id]
        except KeyError as exc:
            raise LockerError("This folder is not protected yet.") from exc

    def get_folder_by_path(self, folder_path: Path) -> ProtectedFolder:
        return self.get_folder(self.folder_id(folder_path))

    @staticmethod
    def folder_id(folder: Path) -> str:
        normalized = os.path.normcase(str(folder.expanduser().resolve()))
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    @staticmethod
    def _validate_new_password(password: str) -> None:
        if not password:
            raise PasswordError("Password cannot be empty.")
        if len(password) < 8:
            raise PasswordError("Password must be at least 8 characters.")

    @staticmethod
    def _resolve_existing_folder(folder_path: Path) -> Path:
        try:
            folder = folder_path.expanduser().resolve(strict=True)
        except FileNotFoundError as exc:
            raise FolderNotFoundError("Folder does not exist.") from exc
        except PermissionError as exc:
            raise PermissionDeniedError("Unable to access the folder.") from exc

        if not folder.is_dir():
            raise FolderNotFoundError("The specified path is not a folder.")
        return folder

    @staticmethod
    def _ensure_folder_exists(folder: Path) -> None:
        if not folder.exists() or not folder.is_dir():
            raise FolderNotFoundError("Folder does not exist.")