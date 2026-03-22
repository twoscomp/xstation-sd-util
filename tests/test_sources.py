from __future__ import annotations

from pathlib import Path

import pytest

from xstation_sd_util.sources.local import LocalSource, _get_stem, _get_suffix


class TestGetSuffix:
    @pytest.mark.parametrize("filename,expected", [
        ("game.rar", ".rar"),
        ("game.7z", ".7z"),
        ("game.zip", ".zip"),
        ("game.tar.gz", ".tar.gz"),
        ("game.tar.bz2", ".tar.bz2"),
        ("game.tgz", ".tgz"),
        ("game.tar", ".tar"),
        ("game.txt", None),
        ("game.bin", None),
    ])
    def test_get_suffix(self, filename, expected):
        assert _get_suffix(Path(filename)) == expected


class TestGetStem:
    @pytest.mark.parametrize("filename,expected", [
        ("game.rar", "game"),
        ("game.tar.gz", "game"),
        ("game.tar.bz2", "game"),
        ("Ape Escape.zip", "Ape Escape"),
        ("007 Racing.7z", "007 Racing"),
    ])
    def test_get_stem(self, filename, expected):
        assert _get_stem(Path(filename)) == expected


class TestLocalSource:
    def test_lists_archives(self, tmp_path):
        (tmp_path / "Ape Escape.zip").write_text("fake")
        (tmp_path / "007 Racing.rar").write_text("fake")
        (tmp_path / "readme.txt").write_text("not an archive")

        source = LocalSource(tmp_path)
        entries = list(source.list_archives())
        stems = {e.stem for e in entries}
        assert stems == {"Ape Escape", "007 Racing"}

    def test_respects_glob_filter(self, tmp_path):
        (tmp_path / "Ape Escape.zip").write_text("fake")
        (tmp_path / "Battle Arena.zip").write_text("fake")

        source = LocalSource(tmp_path, glob_filter="Ape*.zip")
        entries = list(source.list_archives())
        assert len(entries) == 1
        assert entries[0].stem == "Ape Escape"

    def test_local_path_returned(self, tmp_path):
        p = tmp_path / "game.zip"
        p.write_text("fake")
        source = LocalSource(tmp_path)
        entries = list(source.list_archives())
        assert entries[0].local_path() == p

    def test_size_populated(self, tmp_path):
        p = tmp_path / "game.zip"
        p.write_bytes(b"x" * 1234)
        source = LocalSource(tmp_path)
        entries = list(source.list_archives())
        assert entries[0].size == 1234
