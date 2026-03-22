from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .base import ArchiveEntry, GameSource

ARCHIVE_SUFFIXES = {".rar", ".7z", ".zip", ".tar", ".gz", ".tgz"}


def _get_suffix(path: Path) -> str | None:
    name = path.name.lower()
    for multi in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if name.endswith(multi):
            return multi
    if path.suffix.lower() in ARCHIVE_SUFFIXES:
        return path.suffix.lower()
    return None


def _get_stem(path: Path) -> str:
    name = path.name
    for multi in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if name.lower().endswith(multi):
            return name[: -len(multi)]
    return path.stem


class LocalSource(GameSource):
    def __init__(self, directory: Path, glob_filter: str | None = None) -> None:
        self.directory = directory
        self.glob_filter = glob_filter

    def list_archives(self) -> Iterator[ArchiveEntry]:
        pattern = self.glob_filter or "*"
        for path in sorted(self.directory.glob(pattern)):
            if not path.is_file():
                continue
            suffix = _get_suffix(path)
            if suffix is None:
                continue
            stem = _get_stem(path)
            yield ArchiveEntry(
                stem=stem,
                suffix=suffix,
                size=path.stat().st_size,
                _path=path,
            )
