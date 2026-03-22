from __future__ import annotations

import os
from pathlib import Path

import pytest

from xstation_sd_util.extractors.base import apply_single_folder_strip


def _make_tree(base: Path, structure: dict) -> None:
    """Recursively create directory/file structure from a dict."""
    for name, content in structure.items():
        path = base / name
        if isinstance(content, dict):
            path.mkdir(parents=True, exist_ok=True)
            _make_tree(path, content)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content or "")


class TestApplySingleFolderStrip:
    def test_single_top_dir_is_stripped(self, tmp_path):
        """Single top-level folder should be stripped."""
        dest = tmp_path / "game"
        _make_tree(dest, {
            "Ape Escape": {
                "track1.bin": "data",
                "track1.cue": "data",
            }
        })
        apply_single_folder_strip(dest)
        assert (dest / "track1.bin").exists()
        assert (dest / "track1.cue").exists()
        assert not (dest / "Ape Escape").exists()

    def test_multiple_top_entries_not_stripped(self, tmp_path):
        """Multiple top-level entries should be left as-is."""
        dest = tmp_path / "game"
        _make_tree(dest, {
            "track1.bin": "data",
            "track1.cue": "data",
        })
        apply_single_folder_strip(dest)
        assert (dest / "track1.bin").exists()
        assert (dest / "track1.cue").exists()

    def test_single_file_not_stripped(self, tmp_path):
        """Single top-level file (not a dir) should not be stripped."""
        dest = tmp_path / "game"
        dest.mkdir()
        (dest / "game.iso").write_text("data")
        apply_single_folder_strip(dest)
        assert (dest / "game.iso").exists()

    def test_empty_dest_no_error(self, tmp_path):
        """Empty dest directory should not raise."""
        dest = tmp_path / "game"
        dest.mkdir()
        apply_single_folder_strip(dest)  # should not raise


class TestSkipExisting:
    def test_non_empty_existing_folder_is_skipped(self, tmp_path, mocker):
        """Non-empty existing game folder is skipped when skip_existing=True."""
        from xstation_sd_util.processor import process
        from xstation_sd_util.sources.base import ArchiveEntry, GameSource

        dest = tmp_path / "sdcard"
        game_folder = dest / "A" / "Ape Escape"
        game_folder.mkdir(parents=True)
        (game_folder / "track.bin").write_text("existing")

        class FakeSource(GameSource):
            def list_archives(self):
                yield ArchiveEntry(stem="Ape Escape", suffix=".zip", size=100, _path=None)

        extract_mock = mocker.patch("xstation_sd_util.processor.get_extractor")
        process(FakeSource(), dest, skip_existing=True)
        extract_mock.assert_not_called()

    def test_empty_existing_folder_is_reextracted(self, tmp_path, mocker):
        """Empty existing game folder triggers re-extraction."""
        from xstation_sd_util.processor import process
        from xstation_sd_util.sources.base import ArchiveEntry, GameSource

        dest = tmp_path / "sdcard"
        game_folder = dest / "A" / "Ape Escape"
        game_folder.mkdir(parents=True)
        # folder is empty — treat as failed prior run

        archive_path = tmp_path / "Ape Escape.zip"
        archive_path.write_text("fake zip")

        class FakeSource(GameSource):
            def list_archives(self):
                yield ArchiveEntry(stem="Ape Escape", suffix=".zip", size=100, _path=archive_path)

        fake_extractor = mocker.MagicMock()

        def fake_extract(archive, dest_dir, verbose=False):
            (dest_dir / "track.bin").write_text("data")

        fake_extractor.extract.side_effect = fake_extract
        mocker.patch("xstation_sd_util.processor.get_extractor", return_value=fake_extractor)

        process(FakeSource(), dest, skip_existing=True)
        fake_extractor.extract.assert_called_once()
