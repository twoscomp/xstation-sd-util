from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import Extractor


def _find_7z() -> str | None:
    for name in ("7z", "7za", "7zz", "7zr"):
        found = shutil.which(name)
        if found:
            return found
    return None


class SevenZipExtractor(Extractor):
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        binary = _find_7z()
        if binary:
            cmd = [binary, "x", "-y", f"-o{dest_dir}", str(archive_path)]
            result = subprocess.run(cmd, capture_output=not verbose, text=True)
            if result.returncode != 0:
                stderr = result.stderr if not verbose else ""
                raise RuntimeError(f"7z exited {result.returncode}: {stderr.strip()}")
            return

        import py7zr

        with py7zr.SevenZipFile(archive_path, mode="r") as sz:
            if verbose:
                for name in sz.getnames():
                    print(f"  {name}")
                sz.reset()
            sz.extractall(path=dest_dir)

    def uncompressed_size(self, archive_path: Path) -> int:
        try:
            import py7zr

            with py7zr.SevenZipFile(archive_path, mode="r") as sz:
                size = sz.archiveinfo().uncompressed
                return int(size) if size is not None else -1
        except Exception:
            return -1
