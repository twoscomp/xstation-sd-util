from __future__ import annotations

import shutil
from pathlib import Path

from .base import Extractor


def _check_unrar() -> None:
    if shutil.which("unrar") is None and shutil.which("bsdtar") is None:
        raise RuntimeError(
            "RAR archives found but neither 'unrar' nor 'bsdtar' is installed.\n"
            "Install with: apt install unrar  /  brew install rar"
        )


class RarExtractor(Extractor):
    def extract(self, archive_path: Path, dest_dir: Path, verbose: bool = False) -> None:
        import rarfile

        _check_unrar()
        with rarfile.RarFile(archive_path) as rf:
            for member in rf.infolist():
                if verbose:
                    print(f"  {member.filename}")
                rf.extract(member, dest_dir)
