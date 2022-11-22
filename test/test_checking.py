from pathlib import Path

import bib_lookup


_CWD = Path(__file__).absolute().parent

_INPUT_FILE = _CWD / "invalid_items.bib"


def test_checking():
    bl = bib_lookup.BibLookup()
    err_lines = bl.check_bib_file(_INPUT_FILE)
    assert err_lines == [3, 16, 45]
