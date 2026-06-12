"""Command-line interface for scripted folder locker use."""

from __future__ import annotations

import argparse
import getpass
from pathlib import Path

from .config import default_data_dir
from .errors import PasswordError
from .factory import create_locker


def prompt_new_password() -> str:
    """Prompt for and confirm a new password."""

    password = getpass.getpass("New password: ")
    confirmation = getpass.getpass("Confirm new password: ")
    if password != confirmation:
        raise PasswordError("Passwords do not match.")
    return password


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments."""

    data_parent = argparse.ArgumentParser(add_help=False)
    data_parent.add_argument(
        "--data-dir",
        type=Path,
        default=argparse.SUPPRESS,
        help="Directory for locker metadata and logs.",
    )

    parser = argparse.ArgumentParser(
        description="Password-protected folder locker for Windows.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir(),
        help="Directory for locker metadata and logs.",
    )

    subparsers = parser.add_subparsers(dest="command")

    create_parser = subparsers.add_parser(
        "create",
        parents=[data_parent],
        help="Protect a folder.",
    )
    create_parser.add_argument("folder", type=Path)

    lock_parser = subparsers.add_parser(
        "lock",
        parents=[data_parent],
        help="Hide a protected folder.",
    )
    lock_parser.add_argument("folder", type=Path)

    unlock_parser = subparsers.add_parser(
        "unlock",
        parents=[data_parent],
        help="Unhide a folder.",
    )
    unlock_parser.add_argument("folder", type=Path)

    change_parser = subparsers.add_parser(
        "change-password",
        parents=[data_parent],
        help="Change a protected folder password.",
    )
    change_parser.add_argument("folder", type=Path)

    list_parser = subparsers.add_parser(
        "list",
        parents=[data_parent],
        help="List protected folders.",
    )
    list_parser.set_defaults(command="list")

    return parser


def run_cli(args: argparse.Namespace) -> str:
    """Run one CLI command and return a user-facing result."""

    locker = create_locker(args.data_dir.expanduser().resolve())

    if args.command == "create":
        locker.create(args.folder, prompt_new_password())
        return "Protected folder created."

    if args.command == "lock":
        folder = locker.get_folder_by_path(args.folder)
        locker.lock(folder.folder_id)
        return "Folder locked and hidden."

    if args.command == "unlock":
        folder = locker.get_folder_by_path(args.folder)
        locker.unlock(folder.folder_id, getpass.getpass("Password: "))
        return "Folder unlocked and visible."

    if args.command == "change-password":
        folder = locker.get_folder_by_path(args.folder)
        current_password = getpass.getpass("Current password: ")
        new_password = prompt_new_password()
        locker.change_password(folder.folder_id, current_password, new_password)
        return "Password changed."

    if args.command == "list":
        rows = locker.list_folders()
        if not rows:
            return "No protected folders yet."
        return "\n".join(f"{row.status:8} {row.path}" for row in rows)

    raise ValueError(f"Unsupported command: {args.command}")
