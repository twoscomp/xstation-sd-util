from __future__ import annotations

import tarfile
import zipfile
from io import BytesIO
from pathlib import Path


def _make_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)


def _make_tar(path: Path, files: dict[str, bytes]) -> None:
    with tarfile.open(path, "w:gz") as tf:
        for name, data in files.items():
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            tf.addfile(info, BytesIO(data))


class TestZipUncompressedSize:
    def test_returns_sum_of_file_sizes(self, tmp_path):
        from xstation_sd_util.extractors.zip import ZipExtractor

        archive = tmp_path / "test.zip"
        _make_zip(archive, {"a.bin": b"x" * 100, "b.bin": b"y" * 200})
        assert ZipExtractor().uncompressed_size(archive) == 300

    def test_returns_minus_one_on_bad_file(self, tmp_path):
        from xstation_sd_util.extractors.zip import ZipExtractor

        bad = tmp_path / "bad.zip"
        bad.write_bytes(b"not a zip")
        assert ZipExtractor().uncompressed_size(bad) == -1


class TestTarUncompressedSize:
    def test_returns_sum_of_file_sizes(self, tmp_path):
        from xstation_sd_util.extractors.tar import TarExtractor

        archive = tmp_path / "test.tar.gz"
        _make_tar(archive, {"a.bin": b"x" * 150, "b.bin": b"y" * 50})
        assert TarExtractor().uncompressed_size(archive) == 200

    def test_returns_minus_one_on_bad_file(self, tmp_path):
        from xstation_sd_util.extractors.tar import TarExtractor

        bad = tmp_path / "bad.tar.gz"
        bad.write_bytes(b"not a tar")
        assert TarExtractor().uncompressed_size(bad) == -1
