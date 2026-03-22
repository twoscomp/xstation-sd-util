from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class ArchiveEntry:
    stem: str       # becomes the game folder name
    suffix: str     # ".rar", ".tar.gz", ".7z", ".zip"
    size: int       # bytes; -1 if unknown
    _path: Path | None = None  # set by LocalSource

    def local_path(self) -> Path | None:
        return self._path

    def download(self, dest: Path) -> Path:
        """Download archive to dest directory. Returns path to downloaded file."""
        raise NotImplementedError


class GameSource(ABC):
    @abstractmethod
    def list_archives(self) -> Iterator[ArchiveEntry]:
        """Yield ArchiveEntry for each archive in the source."""
        ...
