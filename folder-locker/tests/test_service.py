from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from folder_locker_app.errors import PermissionDeniedError
from folder_locker_app.models import ProtectedFolder
from folder_locker_app.security import PasswordHasher
from folder_locker_app.service import FolderLocker


class FakeStore:
    def __init__(self, folders: dict[str, ProtectedFolder]) -> None:
        self.folders = folders

    def load(self) -> dict[str, ProtectedFolder]:
        return dict(self.folders)

    def save(self, folders: dict[str, ProtectedFolder]) -> None:
        self.folders = dict(folders)


class FakeAttributes:
    def __init__(self) -> None:
        self.locked_paths: set[Path] = set()
        self.hide_calls = 0
        self.unhide_calls = 0

    def is_locked(self, path: Path) -> bool:
        return path in self.locked_paths

    def hide(self, path: Path) -> None:
        self.hide_calls += 1
        self.locked_paths.add(path)

    def unhide(self, path: Path) -> None:
        self.unhide_calls += 1
        self.locked_paths.discard(path)


class FakeAccessControl:
    def __init__(self, *, fail_restrict: bool = False) -> None:
        self.fail_restrict = fail_restrict
        self.restricted_paths: set[Path] = set()
        self.restrict_calls = 0

    def is_restricted(self, path: Path) -> bool:
        return path in self.restricted_paths

    def restrict(self, path: Path) -> None:
        self.restrict_calls += 1
        if self.fail_restrict:
            raise PermissionDeniedError("Unable to restrict folder access.")
        self.restricted_paths.add(path)

    def allow(self, path: Path) -> None:
        self.restricted_paths.discard(path)


class FolderLockerLockTests(unittest.TestCase):
    def make_locker(
        self,
        folder_path: Path,
        *,
        fail_restrict: bool = False,
    ) -> tuple[FolderLocker, FakeAttributes, FakeAccessControl]:
        folder = ProtectedFolder(
            folder_id="folder-1",
            path=folder_path,
            password=PasswordHasher.create("correct horse battery staple"),
        )
        attributes = FakeAttributes()
        access_control = FakeAccessControl(fail_restrict=fail_restrict)
        locker = FolderLocker(FakeStore({folder.folder_id: folder}), attributes, access_control)
        return locker, attributes, access_control

    def test_lock_rolls_back_hidden_attributes_when_restriction_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder_path = Path(temp_dir)
            locker, attributes, access_control = self.make_locker(
                folder_path,
                fail_restrict=True,
            )

            with self.assertRaises(PermissionDeniedError):
                locker.lock("folder-1")

            self.assertFalse(attributes.is_locked(folder_path))
            self.assertFalse(access_control.is_restricted(folder_path))
            self.assertEqual(attributes.hide_calls, 1)
            self.assertEqual(attributes.unhide_calls, 1)

    def test_lock_hides_and_restricts_folder_when_all_steps_succeed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            folder_path = Path(temp_dir)
            locker, attributes, access_control = self.make_locker(folder_path)

            locker.lock("folder-1")

            self.assertTrue(attributes.is_locked(folder_path))
            self.assertTrue(access_control.is_restricted(folder_path))
            self.assertEqual(attributes.hide_calls, 1)
            self.assertEqual(access_control.restrict_calls, 1)


if __name__ == "__main__":
    unittest.main()
