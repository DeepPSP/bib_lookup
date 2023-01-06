"""
"""

from pathlib import Path

import pytest

from bib_lookup import BibLookup


_CWD = Path(__file__).resolve().parent

_SAMPLE_INPUT_FILE = _CWD.parent / "sample-files" / "sample_input.txt"
_SAMPLE_INPUTS = _SAMPLE_INPUT_FILE.read_text().splitlines()
_EXPECTED_OUTPUT_FILE = _CWD.parent / "sample-files" / "expected_output.bib"
_EXPECTED_OUTPUTS = _EXPECTED_OUTPUT_FILE.read_text().strip(" \n")
_OUTPUT_FILE_1 = _CWD.parent / "tmp" / "test_io_output_1.bib"
_OUTPUT_FILE_1.parent.mkdir(exist_ok=True)
_OUTPUT_FILE_2 = _CWD.parent / "tmp" / "test_io_output_2.bib"

_LARGE_DATABASE_FILE = _CWD.parent / "sample-files" / "large_database.bib"

_SOURCE_FILE = _CWD.parent / "sample-files" / "sample-source.tex"
_SOURCE_FILE_LIST = [_SOURCE_FILE]
_SOURCE_FILE_LIST.extend(
    [
        _CWD.parent / "sample-files" / f"sample-source-{item}.tex"
        for item in ["sub1", "sub2", "sub2-1", "sub2-2"]
    ]
)
_SOURCE_FILE_LIST.append(_CWD.parent / "sample-files" / "sample-source-subdir")
_SIMPLIFIED_OUTPUT_FILE = _CWD.parent / "tmp" / "test_io_simplified_output.bib"


def test_io_from_file():
    if _OUTPUT_FILE_1.exists():
        _OUTPUT_FILE_1.unlink()
    bl = BibLookup(output_file=_OUTPUT_FILE_1)
    lookup_result = bl(_SAMPLE_INPUT_FILE, timeout=1000)
    lookup_result = bl(str(_SAMPLE_INPUT_FILE), timeout=1000)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bib_identifier, bib_item = bl[1], bl[bl[1]]
    bl.save([0, 2])
    assert len(bl) == 1
    assert (bib_identifier, bib_item) == (bl[0], bl[bl[0]])
    bl.save()
    assert len(bl) == 0
    bl.save()
    _OUTPUT_FILE_1.unlink()

    bib_items = bl.read_bib_file(_LARGE_DATABASE_FILE, cache=True)
    assert len(bib_items) == len(bl) == 608
    bl.clear_cache()
    assert len(bl) == 0


def test_io_from_list():
    if _OUTPUT_FILE_2.exists():
        _OUTPUT_FILE_2.unlink()
    bl = BibLookup(output_file=_OUTPUT_FILE_2)
    lookup_result = bl(_SAMPLE_INPUTS, timeout=1000)
    assert lookup_result == _EXPECTED_OUTPUTS
    assert len(bl) == 3
    bl.save(bl[0])
    assert len(bl) == 2
    bl.save(0)
    bl.save()
    assert _OUTPUT_FILE_2.read_text().strip(" \n") == _EXPECTED_OUTPUTS
    bl.clear_cache()
    bl.save()
    _OUTPUT_FILE_2.unlink()


def test_pop():
    bl = BibLookup()
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
    output_file = _LARGE_DATABASE_FILE.parent / (
        _LARGE_DATABASE_FILE.stem + "_simplified.bib"
    )
    assert output_file.is_file()
    output_file.unlink()
    del output_file

    if _SIMPLIFIED_OUTPUT_FILE.exists():
        _SIMPLIFIED_OUTPUT_FILE.unlink()
    BibLookup.simplify_bib_file(
        tex_sources=_SOURCE_FILE,
        bib_file=_LARGE_DATABASE_FILE,
        output_file=_SIMPLIFIED_OUTPUT_FILE,
    )

    if _SIMPLIFIED_OUTPUT_FILE.exists():
        _SIMPLIFIED_OUTPUT_FILE.unlink()
    BibLookup.simplify_bib_file(
        tex_sources=_SOURCE_FILE_LIST,
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
