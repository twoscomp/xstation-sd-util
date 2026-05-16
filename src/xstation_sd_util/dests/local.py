from __future__ import annotations

import os
import shutil
from pathlib import Path

from ..organizer import alpha_folder
from .base import GameDest


def _dest_path(root: Path, stem: str, flat: bool) -> Path:
    if flat:
        return root / stem
    return root / alpha_folder(stem) / stem


def _is_non_empty(path: Path) -> bool:
    return path.exists() and any(path.iterdir())


class LocalDest(GameDest):
    def __init__(self, root: Path) -> None:
        self.root = root

    def is_non_empty(self, stem: str, flat: bool) -> bool:
        return _is_non_empty(_dest_path(self.root, stem, flat))

    def place_game(self, tmp_game_dir: Path, stem: str, flat: bool) -> None:
        game_dest = _dest_path(self.root, stem, flat)
        game_dest.parent.mkdir(parents=True, exist_ok=True)
        if game_dest.exists():
            shutil.rmtree(game_dest)
        os.rename(tmp_game_dir, game_dest)

    def ensure_root(self, dry_run: bool) -> None:
        if not dry_run:
            self.root.mkdir(parents=True, exist_ok=True)

    def path_display(self, stem: str, flat: bool) -> str:
        if flat:
            return f"{stem}/"
        return f"{alpha_folder(stem)}/{stem}/"

    def default_tmp_base(self) -> Path:
        return self.root / ".xstation_tmp"

    def space_check_path(self) -> Path:
        return self.root
