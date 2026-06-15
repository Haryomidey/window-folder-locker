"""Top-level application entry point."""

from __future__ import annotations

import logging
import sys

from .cli import build_parser, run_cli
from .errors import LockerError
from .gui import run_gui


def main() -> int:
    """Run the GUI by default, or the CLI when a command is supplied."""

    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        return run_gui(args.data_dir)

    try:
        print(run_cli(args))
        return 0
    except LockerError as exc:
        logging.error("Command failed: %s", exc)
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled.", file=sys.stderr)
        return 130