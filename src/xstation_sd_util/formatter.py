from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from .config import FORMAT_SD_INSTALL_MSG, SYSTEM_FOLDER

# bin/ directory at the project root (one level above src/)
_BIN_DIR = Path(__file__).parent.parent.parent / "bin"


def _find_format_sd() -> str | None:
    """Search for format_sd: repo bin/ first, then PATH."""
    for candidate in (
        _BIN_DIR / "format_sd",
        _BIN_DIR / "SDCardFormatterv1.0.3_Linux_x86_64" / "format_sd",
    ):
        if candidate.is_file():
            return str(candidate)
    return shutil.which("format_sd")


def check_format_sd() -> None:
    if _find_format_sd() is None:
        print(FORMAT_SD_INSTALL_MSG)
        sys.exit(1)


def _get_device_mounts(device: str) -> list[tuple[str, str]]:
    """Return [(source, mountpoint), ...] for device and its partitions."""
    mounts: list[tuple[str, str]] = []
    try:
        with open("/proc/mounts") as f:
            for line in f:
                parts = line.split()
                if len(parts) >= 2:
                    source, mp = parts[0], parts[1]
                    if source == device or source.startswith(device):
                        mounts.append((source, mp))
    except OSError:
        pass
    return mounts


def unmount_device(device: str, dry_run: bool) -> list[tuple[str, str]]:
    """Unmount all partitions of device. Returns the list of (source, mountpoint) pairs."""
    mounts = _get_device_mounts(device)
    for source, mp in mounts:
        if dry_run:
            print(f"Would unmount: {source} from {mp}")
            continue
        result = subprocess.run(["umount", source], capture_output=True, text=True)
        if result.returncode != 0:
            stderr = result.stderr
            if "permission" in stderr.lower() or "Operation not permitted" in stderr:
                raise PermissionError(stderr)
            raise RuntimeError(f"Failed to unmount {source}: {stderr}")
    return mounts


def format_device(device: str, label: str, dry_run: bool) -> None:
    if dry_run:
        print(f"Would run: format_sd -l {label} {device}")
        return
    if not Path(device).exists():
        raise FileNotFoundError(f"Device not found: {device}")
    binary = _find_format_sd() or "format_sd"
    result = subprocess.run(
        [binary, "-l", label, device],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr
        if "permission" in stderr.lower() or "Operation not permitted" in stderr:
            raise PermissionError(stderr)
        raise RuntimeError(stderr)


def mount_device(device: str, mountpoint: str, dry_run: bool) -> None:
    """Mount the formatted device at mountpoint, trying {device}1 then {device}."""
    if dry_run:
        print(f"Would mount: {device} at {mountpoint}")
        return
    Path(mountpoint).mkdir(parents=True, exist_ok=True)
    for candidate in (f"{device}1", device):
        if not Path(candidate).exists():
            continue
        result = subprocess.run(
            ["mount", candidate, mountpoint],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return
        stderr = result.stderr
        if "permission" in stderr.lower() or "Operation not permitted" in stderr:
            raise PermissionError(stderr)
    raise RuntimeError(f"Could not mount {device} at {mountpoint}")


def create_system_dir(mountpoint: Path, dry_run: bool) -> Path:
    if not mountpoint.is_dir():
        raise NotADirectoryError(f"Not a directory: {mountpoint}")
    dest = mountpoint / SYSTEM_FOLDER
    if dry_run:
        print(f"Would create: {dest}")
        return dest
    dest.mkdir(exist_ok=True)
    return dest
