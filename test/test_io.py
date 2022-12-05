"""
"""

import os
from pathlib import Path

import pytest

from bib_lookup import BibLookup


_CWD = Path(__file__).resolve().parent

_SAMPLE_INPUT_FILE = _CWD / "sample-files" / "sample_input.txt"
_SAMPLE_INPUTS = _SAMPLE_INPUT_FILE.read_text().splitlines()
_EXPECTED_OUTPUT_FILE = _CWD / "sample-files" / "expected_output.bib"
_EXPECTED_OUTPUTS = _EXPECTED_OUTPUT_FILE.read_text().strip(" \n")
_OUTPUT_FILE = _CWD / "sample-files" / "test_output.bib"

_LARGE_DATABASE_FILE = _CWD / "sample-files" / "large_database.bib"

_SOURCE_FILE = _CWD / "sample-files" / "sample-source.tex"
_SIMPLIFIED_OUTPUT_FILE = _CWD / "tmp" / "simplified_output.bib"


bl = BibLookup(output_file=_OUTPUT_FILE)


def test_io_from_file():
    lookup_result = bl(_SAMPLE_INPUT_FILE, timeout=1000)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bib_identifier, bib_item = bl[1], bl[bl[1]]
    bl.save([0, 2])
    assert len(bl) == 1
    assert (bib_identifier, bib_item) == (bl[0], bl[bl[0]])
    bl.save()
    assert len(bl) == 0
    bl.save()
    os.remove(_OUTPUT_FILE)

    lookup_result = bl(str(_SAMPLE_INPUT_FILE), timeout=1000)

    bib_items = bl.read_bib_file(_LARGE_DATABASE_FILE, cache=True)
    assert len(bib_items) == len(bl) == 608
    bl.clear_cache()
    assert len(bl) == 0


def test_io_from_list():
    lookup_result = bl(_SAMPLE_INPUTS, timeout=1000)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bl.save(bl[0])
    assert len(bl) == 2
    bl.save(1)
    bl.save()
    assert _OUTPUT_FILE.read_text().strip(" \n") == _EXPECTED_OUTPUTS
    bl.clear_cache()
    os.remove(_OUTPUT_FILE)


def test_pop():
    lookup_result = bl(_SAMPLE_INPUTS, timeout=1000)
    bl.pop(0)
    bl.pop([0])
    bl.pop(bl[0])


def test_simplify_bib_file():
    BibLookup.simplify_bib_file(
        tex_sources=_SOURCE_FILE,
        bib_file=_LARGE_DATABASE_FILE,
        output_file=None,
    )

    if _SIMPLIFIED_OUTPUT_FILE.exists():
        _SIMPLIFIED_OUTPUT_FILE.unlink()
    BibLookup.simplify_bib_file(
        tex_sources=_SOURCE_FILE,
        bib_file=_LARGE_DATABASE_FILE,
        output_file=_SIMPLIFIED_OUTPUT_FILE,
    )

    with pytest.raises(FileExistsError, match="Output file \042.+\042 already exists"):
        BibLookup.simplify_bib_file(
            tex_sources=_SOURCE_FILE,
            bib_file=_LARGE_DATABASE_FILE,
            output_file=_SIMPLIFIED_OUTPUT_FILE,
        )
        _SIMPLIFIED_OUTPUT_FILE.unlink()
