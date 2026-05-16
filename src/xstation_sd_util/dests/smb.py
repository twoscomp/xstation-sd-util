from __future__ import annotations

import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse

from ..organizer import alpha_folder
from .base import GameDest

try:
    import smbclient  # type: ignore
    import smbclient.path  # type: ignore
    HAS_SMB = True
except ImportError:
    HAS_SMB = False


def _smb_upload_tree(local_dir: Path, unc: str) -> None:
    import smbclient
    smbclient.makedirs(unc, exist_ok=True)
    for item in local_dir.iterdir():
        child_unc = unc + "\\" + item.name
        if item.is_dir():
            _smb_upload_tree(item, child_unc)
        else:
            with open(item, "rb") as src:
                with smbclient.open_file(child_unc, mode="wb") as dst:
                    while chunk := src.read(1 << 20):
                        dst.write(chunk)


def _smb_rmtree(unc: str) -> None:
    import smbclient
    for entry in smbclient.scandir(unc):
        child = unc + "\\" + entry.name
        if entry.is_dir(follow_symlinks=False):
            _smb_rmtree(child)
            smbclient.rmdir(child)
        else:
            smbclient.remove(child)
    smbclient.rmdir(unc)


class SmbDest(GameDest):
    def __init__(
        self,
        url: str,
        username: str | None = None,
        password: str | None = None,
        domain: str | None = None,
    ) -> None:
        if not HAS_SMB:
            raise ImportError(
                "SMB support requires: pip install xstation-sd-util[smb]"
            )
        parsed = urlparse(url)
        self.server = parsed.hostname
        self.share = parsed.path.lstrip("/").split("/")[0]
        rest = "/".join(parsed.path.lstrip("/").split("/")[1:])
        self.remote_path = rest or ""
        raw_username = username or parsed.username
        self.password = password or parsed.password

        if domain and raw_username and "\\" not in raw_username:
            self.username = f"{domain}\\{raw_username}"
        else:
            self.username = raw_username

        smbclient.register_session(
            self.server,
            username=self.username,
            password=self.password,
        )

    def _unc(self, *parts: str) -> str:
        base = f"\\\\{self.server}\\{self.share}"
        if self.remote_path:
            base += "\\" + self.remote_path.replace("/", "\\")
        for p in parts:
            base += "\\" + p.replace("/", "\\")
        return base

    def _game_unc(self, stem: str, flat: bool) -> str:
        if flat:
            return self._unc(stem)
        return self._unc(alpha_folder(stem), stem)

    def is_non_empty(self, stem: str, flat: bool) -> bool:
        import smbclient
        unc = self._game_unc(stem, flat)
        try:
            if not smbclient.path.isdir(unc):
                return False
            return any(True for _ in smbclient.scandir(unc))
        except Exception:
            return False

    def place_game(self, tmp_game_dir: Path, stem: str, flat: bool) -> None:
        import smbclient
        game_unc = self._game_unc(stem, flat)
        parent_unc = self._unc() if flat else self._unc(alpha_folder(stem))
        smbclient.makedirs(parent_unc, exist_ok=True)
        if smbclient.path.exists(game_unc):
            _smb_rmtree(game_unc)
        _smb_upload_tree(tmp_game_dir, game_unc)

    def ensure_root(self, dry_run: bool) -> None:
        if dry_run:
            return
        import smbclient
        smbclient.makedirs(self._unc(), exist_ok=True)

    def path_display(self, stem: str, flat: bool) -> str:
        unc = self._game_unc(stem, flat)
        return unc.replace("\\", "/").lstrip("/") + "/"

    def default_tmp_base(self) -> Path:
        return Path(tempfile.gettempdir()) / "xstation_sd_tmp"

    def space_check_path(self) -> Path:
        return Path(tempfile.gettempdir())
