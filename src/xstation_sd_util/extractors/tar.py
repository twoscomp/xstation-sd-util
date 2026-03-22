from __future__ import annotations

import tarfile
from pathlib import Path

from .base import Extractor


class TarExtractor(Extractor):
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        with tarfile.open(archive_path) as tf:
            for member in tf.getmembers():
                if verbose:
                    print(f"  {member.name}")
                tf.extract(member, dest_dir, filter="data")

    def uncompressed_size(self, archive_path: Path) -> int:
        try:
            with tarfile.open(archive_path) as tf:
                return sum(m.size for m in tf.getmembers() if m.isfile())
        except Exception:
            return -1
