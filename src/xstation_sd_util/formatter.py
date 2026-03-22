from __future__ import annotations

from pathlib import Path

from .config import SYSTEM_FOLDER


def create_system_dir(mountpoint: Path, dry_run: bool) -> Path:
    if not mountpoint.is_dir():
        raise NotADirectoryError(f"Not a directory: {mountpoint}")
    dest = mountpoint / SYSTEM_FOLDER
    if dry_run:
        print(f"Would create: {dest}")
        return dest
    dest.mkdir(exist_ok=True)
    return dest
