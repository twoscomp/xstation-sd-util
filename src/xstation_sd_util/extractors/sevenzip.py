from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from .base import Extractor


def _patch_py7zr_timestamps() -> None:
    """Monkey-patch py7zr to handle archives where lastwritetime is None.

    py7zr catches KeyError but not TypeError when constructing ArchiveTimestamp,
    so archives with undefined timestamps crash with int(None). Replace the name
    in the py7zr.py7zr module namespace with a safe wrapper.
    """
    try:
        import py7zr.py7zr as _m
        import py7zr.helpers as _h

        if getattr(_m.ArchiveTimestamp, "_safe", False):
            return  # already patched

        _orig = _h.ArchiveTimestamp

        class _NullTimestamp:
            _safe = True

            def totimestamp(self) -> None:
                return None

        def _safe_timestamp(value):  # type: ignore[return]
            return _NullTimestamp() if value is None else _orig(value)

        _safe_timestamp._safe = True  # type: ignore[attr-defined]
        _m.ArchiveTimestamp = _safe_timestamp  # type: ignore[attr-defined]
    except Exception:
        pass


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

        _patch_py7zr_timestamps()
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
