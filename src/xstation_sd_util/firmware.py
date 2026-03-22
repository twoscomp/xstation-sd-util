from __future__ import annotations

import json
import shutil
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from .config import FIRMWARE_FILES, GITHUB_RELEASES_API


def install_firmware(
    dest_dir: Path,
    firmware_path: Path | None,
    skip_firmware: bool,
    dry_run: bool,
) -> None:
    if skip_firmware:
        print("Skipping firmware installation.")
        return
    if firmware_path is not None:
        copy_firmware_from_path(firmware_path, dest_dir, dry_run)
    else:
        download_latest_firmware(dest_dir, dry_run)


def copy_firmware_from_path(source: Path, dest_dir: Path, dry_run: bool) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Firmware source not found: {source}")
    if dry_run:
        print(f"Would copy firmware from {source} to {dest_dir}")
        return
    if source.is_dir():
        for name in FIRMWARE_FILES:
            src_file = source / name
            if not src_file.exists():
                raise RuntimeError(f"'{name}' not found in firmware directory: {source}")
        for name in FIRMWARE_FILES:
            shutil.copy2(source / name, dest_dir / name)
    elif source.suffix == ".zip":
        _extract_firmware_from_zip(source, dest_dir)
    else:
        raise ValueError("--firmware must be a directory or .zip file")


def download_latest_firmware(dest_dir: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"Would download latest firmware from {GITHUB_RELEASES_API} to {dest_dir}")
        return
    with urllib.request.urlopen(GITHUB_RELEASES_API, timeout=15) as resp:
        data = json.loads(resp.read())
    assets = data.get("assets", [])
    if not assets:
        raise RuntimeError("No assets found in latest GitHub release")
    asset_map = {asset["name"]: asset["browser_download_url"] for asset in assets}
    if all(name in asset_map for name in FIRMWARE_FILES):
        for name in FIRMWARE_FILES:
            urllib.request.urlretrieve(asset_map[name], dest_dir / name)
    else:
        zip_asset = next(
            (a for a in assets if a["name"].endswith(".zip")),
            None,
        )
        if zip_asset is None:
            raise RuntimeError("No firmware assets found in latest GitHub release")
        with tempfile.TemporaryDirectory() as tmp:
            zip_path = Path(tmp) / zip_asset["name"]
            urllib.request.urlretrieve(zip_asset["browser_download_url"], zip_path)
            _extract_firmware_from_zip(zip_path, dest_dir)


def _extract_firmware_from_zip(zip_path: Path, dest_dir: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            for file_name in FIRMWARE_FILES:
                match = next(
                    (n for n in names if Path(n).name == file_name),
                    None,
                )
                if match is None:
                    raise RuntimeError(f"'{file_name}' not found inside firmware zip")
                zf.extract(match, tmp_path)
                shutil.copy2(tmp_path / match, dest_dir / file_name)
