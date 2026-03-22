from __future__ import annotations

from pathlib import Path

import pytest

from xstation_sd_util.formatter import create_system_dir


def test_create_system_dir_creates_folder(tmp_path):
    result = create_system_dir(tmp_path, dry_run=False)
    assert result.is_dir()
    assert result.name == "00xstation"


def test_create_system_dir_raises_for_bad_mountpoint(tmp_path):
    bad = tmp_path / "not_a_dir"
    with pytest.raises(NotADirectoryError):
        create_system_dir(bad, dry_run=False)


def test_create_system_dir_dry_run_does_not_create(tmp_path, capsys):
    result = create_system_dir(tmp_path, dry_run=True)
    assert not result.exists()
    assert "Would create" in capsys.readouterr().out
