from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xstation_sd_util.firmware import (
    _extract_firmware_from_zip,
    copy_firmware_from_path,
    download_latest_firmware,
    install_firmware,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_zip(tmp_path: Path, members: dict[str, bytes], *, prefix: str = "") -> Path:
    """Build a .zip archive containing the given members."""
    zip_path = tmp_path / "firmware.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for name, data in members.items():
            zf.writestr(f"{prefix}{name}" if prefix else name, data)
    return zip_path


def _fake_release(assets: list[dict]) -> bytes:
    return json.dumps({"assets": assets}).encode()


# ---------------------------------------------------------------------------
# copy_firmware_from_path — directory source
# ---------------------------------------------------------------------------

def test_copy_firmware_from_directory(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "update.bin").write_bytes(b"upd")
    (src / "loader.bin").write_bytes(b"ldr")

    dest = tmp_path / "dest"
    dest.mkdir()
    copy_firmware_from_path(src, dest, dry_run=False)

    assert (dest / "update.bin").read_bytes() == b"upd"
    assert (dest / "loader.bin").read_bytes() == b"ldr"


def test_copy_firmware_from_directory_missing_file(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "update.bin").write_bytes(b"upd")
    # loader.bin intentionally absent

    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(RuntimeError, match="loader.bin"):
        copy_firmware_from_path(src, dest, dry_run=False)


# ---------------------------------------------------------------------------
# copy_firmware_from_path — zip source
# ---------------------------------------------------------------------------

def test_copy_firmware_from_zip(tmp_path):
    zip_path = _make_zip(tmp_path, {"update.bin": b"upd", "loader.bin": b"ldr"})
    dest = tmp_path / "dest"
    dest.mkdir()
    copy_firmware_from_path(zip_path, dest, dry_run=False)

    assert (dest / "update.bin").read_bytes() == b"upd"
    assert (dest / "loader.bin").read_bytes() == b"ldr"


def test_copy_firmware_from_zip_nested(tmp_path):
    zip_path = _make_zip(
        tmp_path,
        {"update.bin": b"upd", "loader.bin": b"ldr"},
        prefix="firmware/v1.0/",
    )
    dest = tmp_path / "dest"
    dest.mkdir()
    copy_firmware_from_path(zip_path, dest, dry_run=False)

    assert (dest / "update.bin").read_bytes() == b"upd"
    assert (dest / "loader.bin").read_bytes() == b"ldr"


# ---------------------------------------------------------------------------
# copy_firmware_from_path — edge cases
# ---------------------------------------------------------------------------

def test_copy_firmware_missing_source_raises(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(FileNotFoundError):
        copy_firmware_from_path(tmp_path / "nope", dest, dry_run=False)


def test_copy_firmware_wrong_type_raises(tmp_path):
    src = tmp_path / "firmware.tar"
    src.write_bytes(b"data")
    dest = tmp_path / "dest"
    dest.mkdir()
    with pytest.raises(ValueError, match="directory or .zip"):
        copy_firmware_from_path(src, dest, dry_run=False)


def test_copy_firmware_dry_run_copies_nothing(tmp_path, capsys):
    src = tmp_path / "src"
    src.mkdir()
    (src / "update.bin").write_bytes(b"upd")
    (src / "loader.bin").write_bytes(b"ldr")

    dest = tmp_path / "dest"
    dest.mkdir()
    copy_firmware_from_path(src, dest, dry_run=True)

    assert not (dest / "update.bin").exists()
    assert not (dest / "loader.bin").exists()
    assert "Would copy" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# download_latest_firmware — individual assets
# ---------------------------------------------------------------------------

def test_download_latest_firmware_individual_assets(tmp_path):
    assets = [
        {"name": "update.bin", "browser_download_url": "http://example.com/update.bin"},
        {"name": "loader.bin", "browser_download_url": "http://example.com/loader.bin"},
    ]
    fake_resp = MagicMock()
    fake_resp.read.return_value = _fake_release(assets)
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)

    retrieved = []

    def fake_urlretrieve(url, dest):
        retrieved.append((url, Path(dest).name))
        Path(dest).write_bytes(b"data")

    with patch("urllib.request.urlopen", return_value=fake_resp):
        with patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            download_latest_firmware(tmp_path, dry_run=False)

    assert len(retrieved) == 2
    names = {r[1] for r in retrieved}
    assert names == {"update.bin", "loader.bin"}


# ---------------------------------------------------------------------------
# download_latest_firmware — zip fallback
# ---------------------------------------------------------------------------

def test_download_latest_firmware_zip_fallback(tmp_path):
    build = tmp_path / "build"
    build.mkdir()
    zip_path = _make_zip(build, {"update.bin": b"upd", "loader.bin": b"ldr"})

    assets = [
        {"name": "firmware.zip", "browser_download_url": "http://example.com/firmware.zip"},
    ]
    fake_resp = MagicMock()
    fake_resp.read.return_value = _fake_release(assets)
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)

    def fake_urlretrieve(url, dest):
        import shutil
        shutil.copy(zip_path, dest)

    dest = tmp_path / "dest"
    dest.mkdir()

    with patch("urllib.request.urlopen", return_value=fake_resp):
        with patch("urllib.request.urlretrieve", side_effect=fake_urlretrieve):
            download_latest_firmware(dest, dry_run=False)

    assert (dest / "update.bin").read_bytes() == b"upd"
    assert (dest / "loader.bin").read_bytes() == b"ldr"


# ---------------------------------------------------------------------------
# download_latest_firmware — error / dry-run
# ---------------------------------------------------------------------------

def test_download_latest_firmware_no_assets_raises(tmp_path):
    fake_resp = MagicMock()
    fake_resp.read.return_value = _fake_release([])
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)

    with patch("urllib.request.urlopen", return_value=fake_resp):
        with pytest.raises(RuntimeError):
            download_latest_firmware(tmp_path, dry_run=False)


def test_download_latest_firmware_dry_run_never_calls_urlopen(tmp_path, capsys):
    with patch("urllib.request.urlopen") as mock_open:
        download_latest_firmware(tmp_path, dry_run=True)
    mock_open.assert_not_called()
    assert "Would download" in capsys.readouterr().out
