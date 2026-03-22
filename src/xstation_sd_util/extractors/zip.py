from __future__ import annotations

import zipfile
from pathlib import Path

from .base import Extractor


class ZipExtractor(Extractor):
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        with zipfile.ZipFile(archive_path) as zf:
            for member in zf.infolist():
                if verbose:
                    print(f"  {member.filename}")
                zf.extract(member, dest_dir)

    def uncompressed_size(self, archive_path: Path) -> int:
        try:
            with zipfile.ZipFile(archive_path) as zf:
                return sum(m.file_size for m in zf.infolist())
        except Exception:
            return -1
