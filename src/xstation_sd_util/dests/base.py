from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path


class GameDest(ABC):
    @abstractmethod
    def is_non_empty(self, stem: str, flat: bool) -> bool:
        """True if the game folder already exists and has content."""

    @abstractmethod
    def place_game(self, tmp_game_dir: Path, stem: str, flat: bool) -> None:
        """Move/upload the local temp game folder to its final destination."""

    @abstractmethod
    def ensure_root(self, dry_run: bool) -> None:
        """Create root directory if needed."""

    @abstractmethod
    def path_display(self, stem: str, flat: bool) -> str:
        """Human-readable destination string for dry-run output."""

    @abstractmethod
    def default_tmp_base(self) -> Path:
        """Fallback local temp dir when --temp-dir is not given."""

    @abstractmethod
    def space_check_path(self) -> Path:
        """Local path for free-space estimation."""
