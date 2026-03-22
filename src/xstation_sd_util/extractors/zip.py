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
