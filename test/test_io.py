import os
from pathlib import Path

try:
    import bib_lookup
except ModuleNotFoundError:
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))
    import bib_lookup


_CWD = Path(__file__).absolute().parent

_SAMPLE_INPUT_FILE = _CWD / "sample_input.txt"
_SAMPLE_INPUTS = _SAMPLE_INPUT_FILE.read_text().splitlines()
_EXPECTED_OUTPUT_FILE = _CWD / "expected_output.bib"
_EXPECTED_OUTPUTS = _EXPECTED_OUTPUT_FILE.read_text().strip(" \n")
_OUTPUT_FILE = _CWD / "test_output.bib"

_LARGE_DATABASE_FILE = _CWD / "large_database.bib"


bl = bib_lookup.BibLookup(output_file=_OUTPUT_FILE)


def test_io_from_file():
    lookup_result = bl(_SAMPLE_INPUT_FILE)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bib_identifier, bib_item = bl[1], bl[bl[1]]
    bl.save([0, 2])
    assert len(bl) == 1
    assert (bib_identifier, bib_item) == (bl[0], bl[bl[0]])
    bl.save()
    assert len(bl) == 0
    os.remove(_OUTPUT_FILE)

    bib_items = bl.read_bib_file(_LARGE_DATABASE_FILE, cache=True)
    assert len(bib_items) == len(bl) == 608
    bl.clear_cache()
    assert len(bl) == 0


def test_io_from_list():
    lookup_result = bl(_SAMPLE_INPUTS)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bl.save(bl[0])
    assert len(bl) == 2
    bl.save()
    assert _OUTPUT_FILE.read_text().strip(" \n") == _EXPECTED_OUTPUTS
    os.remove(_OUTPUT_FILE)


if __name__ == "__main__":
    test_io_from_file()
    test_io_from_list()
