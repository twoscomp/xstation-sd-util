from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Iterator
from urllib.parse import urlparse

from .base import ArchiveEntry, GameSource
from .local import ARCHIVE_SUFFIXES, _get_stem

try:
    import smbclient  # type: ignore
    import smbclient.path  # type: ignore
    HAS_SMB = True
except ImportError:
    HAS_SMB = False


def _smb_suffix(name: str) -> str | None:
    lower = name.lower()
    for multi in (".tar.gz", ".tar.bz2", ".tar.xz"):
        if lower.endswith(multi):
            return multi
    suffix = PurePosixPath(name).suffix.lower()
    return suffix if suffix in ARCHIVE_SUFFIXES else None


class SmbSource(GameSource):
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

        # smbprotocol encodes domain as "DOMAIN\user" in the username field
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

    def list_archives(self) -> Iterator[ArchiveEntry]:
        import smbclient

        root_unc = self._unc()
        for entry in smbclient.scandir(root_unc):
            if not entry.is_file():
                continue
            suffix = _smb_suffix(entry.name)
            if suffix is None:
                continue
            stem = _get_stem(Path(entry.name))
            try:
                size = entry.stat().st_size
            except Exception:
                size = -1
            yield ArchiveEntry(stem=stem, suffix=suffix, size=size)

    def download(self, entry: ArchiveEntry, dest: Path) -> Path:
        import smbclient

        filename = entry.stem + entry.suffix
        unc_path = self._unc(filename)
        out_path = dest / filename
        with smbclient.open_file(unc_path, mode="rb") as src:
            with open(out_path, "wb") as dst:
                while chunk := src.read(1 << 20):
                    dst.write(chunk)
        return out_path
