"""Logging configuration."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import LOG_FILE
from .errors import PermissionDeniedError


def setup_logging(data_dir: Path) -> None:
    """Configure event logging without recording passwords."""

    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=str(data_dir / LOG_FILE),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
            force=True,
        )
    except PermissionError as exc:
        raise PermissionDeniedError("Unable to create the log directory.") from exc
