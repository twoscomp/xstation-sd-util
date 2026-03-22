from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class Extractor(ABC):
    @abstractmethod
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        """Extract archive_path into dest_dir (already created)."""
        ...


def apply_single_folder_strip(dest_dir: Path) -> None:
    """
    If dest_dir contains exactly one subdirectory (and no loose files),
    move its contents up one level and remove the now-empty subdirectory.

    Rule: single top-level folder → strip it.
    Multiple top-level entries → leave as-is.
    """
    entries = list(dest_dir.iterdir())
    if len(entries) != 1 or not entries[0].is_dir():
        return

    inner_dir = entries[0]
    # Move each item in inner_dir up to dest_dir
    for item in list(inner_dir.iterdir()):
        item.rename(dest_dir / item.name)
    inner_dir.rmdir()


def get_extractor(suffix: str) -> Extractor:
    """Return the appropriate extractor for the given suffix."""
    from .tar import TarExtractor
    from .rar import RarExtractor
    from .sevenzip import SevenZipExtractor
    from .zip import ZipExtractor

    suffix = suffix.lower()
    if suffix in (".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz"):
        return TarExtractor()
    if suffix == ".rar":
        return RarExtractor()
    if suffix == ".7z":
        return SevenZipExtractor()
    if suffix == ".zip":
        return ZipExtractor()
    raise ValueError(f"No extractor for suffix: {suffix!r}")
