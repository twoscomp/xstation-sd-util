import pytest
from xstation_sd_util.organizer import alpha_folder


@pytest.mark.parametrize("name,expected", [
    ("Ape Escape", "A"),
    ("ape escape", "A"),
    ("Battle Arena Toshinden", "B"),
    ("007 Racing", "#"),
    ("1Xtreme", "#"),
    ("#Moo", "#"),
    ("  Xenogears", "X"),   # leading spaces stripped
    ("", "#"),
    ("   ", "#"),
    ("Zork", "Z"),
])
def test_alpha_folder(name, expected):
    assert alpha_folder(name) == expected
