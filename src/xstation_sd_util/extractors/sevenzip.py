from __future__ import annotations

from pathlib import Path

from .base import Extractor


class SevenZipExtractor(Extractor):
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        import py7zr

        with py7zr.SevenZipFile(archive_path, mode="r") as sz:
            if verbose:
                for name in sz.getnames():
                    print(f"  {name}")
                sz.reset()
            sz.extractall(path=dest_dir)
