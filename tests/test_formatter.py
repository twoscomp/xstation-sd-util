from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from xstation_sd_util.formatter import (
    _find_format_sd,
    _get_device_mounts,
    check_format_sd,
    create_system_dir,
    format_device,
    mount_device,
    unmount_device,
)


# ---------------------------------------------------------------------------
# _find_format_sd
# ---------------------------------------------------------------------------

def test_find_format_sd_finds_in_bin_subdir(tmp_path):
    subdir = tmp_path / "SDCardFormatterv1.0.3_Linux_x86_64"
    subdir.mkdir()
    binary = subdir / "format_sd"
    binary.touch()
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        result = _find_format_sd()
    assert result == str(binary)


def test_find_format_sd_finds_flat_in_bin(tmp_path):
    binary = tmp_path / "format_sd"
    binary.touch()
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        result = _find_format_sd()
    assert result == str(binary)


def test_find_format_sd_falls_back_to_which(tmp_path):
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        with patch("shutil.which", return_value="/usr/bin/format_sd"):
            result = _find_format_sd()
    assert result == "/usr/bin/format_sd"


def test_find_format_sd_returns_none_when_missing(tmp_path):
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        with patch("shutil.which", return_value=None):
            result = _find_format_sd()
    assert result is None


# ---------------------------------------------------------------------------
# check_format_sd
# ---------------------------------------------------------------------------

def test_check_format_sd_exits_when_missing(tmp_path):
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        with patch("shutil.which", return_value=None):
            with pytest.raises(SystemExit):
                check_format_sd()


def test_check_format_sd_passes_when_found(tmp_path):
    with patch("xstation_sd_util.formatter._BIN_DIR", tmp_path):
        with patch("shutil.which", return_value="/usr/bin/format_sd"):
            check_format_sd()  # should not raise


# ---------------------------------------------------------------------------
# format_device
# ---------------------------------------------------------------------------

def test_format_device_dry_run_never_calls_subprocess(capsys):
    with patch("subprocess.run") as mock_run:
        format_device("/dev/sdc", "xstation", dry_run=True)
    mock_run.assert_not_called()
    assert "Would run" in capsys.readouterr().out


def test_format_device_raises_file_not_found_for_missing_device(tmp_path):
    with pytest.raises(FileNotFoundError):
        format_device(str(tmp_path / "nonexistent"), "xstation", dry_run=False)


def test_format_device_raises_permission_error(tmp_path):
    device = tmp_path / "fake_dev"
    device.touch()
    result = MagicMock(returncode=1, stderr="permission denied")
    with patch("subprocess.run", return_value=result):
        with pytest.raises(PermissionError):
            format_device(str(device), "xstation", dry_run=False)


def test_format_device_raises_runtime_error(tmp_path):
    device = tmp_path / "fake_dev"
    device.touch()
    result = MagicMock(returncode=1, stderr="some error")
    with patch("subprocess.run", return_value=result):
        with pytest.raises(RuntimeError):
            format_device(str(device), "xstation", dry_run=False)


def test_format_device_succeeds(tmp_path):
    device = tmp_path / "fake_dev"
    device.touch()
    result = MagicMock(returncode=0, stderr="")
    with patch("subprocess.run", return_value=result):
        format_device(str(device), "xstation", dry_run=False)


# ---------------------------------------------------------------------------
# _get_device_mounts / unmount_device
# ---------------------------------------------------------------------------

_PROC_MOUNTS = """\
/dev/sda1 / ext4 rw 0 0
/dev/sdc1 /media/card vfat rw 0 0
tmpfs /tmp tmpfs rw 0 0
"""


def test_unmount_device_dry_run_does_not_call_umount(capsys):
    with patch("xstation_sd_util.formatter._get_device_mounts",
               return_value=[("/dev/sdc1", "/media/card")]):
        with patch("subprocess.run") as mock_run:
            unmount_device("/dev/sdc", dry_run=True)
    mock_run.assert_not_called()
    assert "Would unmount" in capsys.readouterr().out


def test_unmount_device_no_mounts_returns_empty():
    with patch("xstation_sd_util.formatter._get_device_mounts", return_value=[]):
        result = unmount_device("/dev/sdc", dry_run=False)
    assert result == []


def test_unmount_device_calls_umount():
    with patch("xstation_sd_util.formatter._get_device_mounts",
               return_value=[("/dev/sdc1", "/media/card")]):
        mock_result = MagicMock(returncode=0)
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            unmount_device("/dev/sdc", dry_run=False)
    mock_run.assert_called_once_with(["umount", "/dev/sdc1"], capture_output=True, text=True)


def test_unmount_device_raises_permission_error():
    with patch("xstation_sd_util.formatter._get_device_mounts",
               return_value=[("/dev/sdc1", "/media/card")]):
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="Operation not permitted")):
            with pytest.raises(PermissionError):
                unmount_device("/dev/sdc", dry_run=False)


def test_unmount_device_raises_runtime_error():
    with patch("xstation_sd_util.formatter._get_device_mounts",
               return_value=[("/dev/sdc1", "/media/card")]):
        with patch("subprocess.run", return_value=MagicMock(returncode=1, stderr="target is busy")):
            with pytest.raises(RuntimeError):
                unmount_device("/dev/sdc", dry_run=False)


# ---------------------------------------------------------------------------
# mount_device
# ---------------------------------------------------------------------------

def test_mount_device_dry_run(tmp_path, capsys):
    with patch("subprocess.run") as mock_run:
        mount_device("/dev/sdc", str(tmp_path / "mnt"), dry_run=True)
    mock_run.assert_not_called()
    assert "Would mount" in capsys.readouterr().out


def test_mount_device_tries_first_partition(tmp_path):
    device = str(tmp_path / "sdc")
    partition = str(tmp_path / "sdc1")
    Path(partition).touch()
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        mount_device(device, str(tmp_path / "mnt"), dry_run=False)
    assert mock_run.call_args[0][0][1] == partition


def test_mount_device_falls_back_to_device(tmp_path):
    device = str(tmp_path / "sdc")
    Path(device).touch()
    mock_result = MagicMock(returncode=0)
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        mount_device(device, str(tmp_path / "mnt"), dry_run=False)
    assert mock_run.call_args[0][0][1] == device


def test_mount_device_raises_runtime_error_when_no_candidates(tmp_path):
    with pytest.raises(RuntimeError):
        mount_device(str(tmp_path / "sdc"), str(tmp_path / "mnt"), dry_run=False)


# ---------------------------------------------------------------------------
# create_system_dir
# ---------------------------------------------------------------------------

def test_create_system_dir_creates_folder(tmp_path):
    result = create_system_dir(tmp_path, dry_run=False)
    assert result.is_dir()
    assert result.name == "00xstation"


def test_create_system_dir_raises_for_bad_mountpoint(tmp_path):
    with pytest.raises(NotADirectoryError):
        create_system_dir(tmp_path / "not_a_dir", dry_run=False)


def test_create_system_dir_dry_run_does_not_create(tmp_path, capsys):
    result = create_system_dir(tmp_path, dry_run=True)
    assert not result.exists()
    assert "Would create" in capsys.readouterr().out
