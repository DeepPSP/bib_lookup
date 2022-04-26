from pathlib import Path

try:
    import bib_lookup
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
    import bib_lookup


_CWD = Path(__file__).absolute().parent

_INPUT_FILE = _CWD / "invalid_items.bib"


def test_checking():
    bl = bib_lookup.BibLookup()
    err_lines = bl.check_bib_file(_INPUT_FILE)
    assert err_lines == [3, 16, 45]


if __name__ == "__main__":
    test_checking()
