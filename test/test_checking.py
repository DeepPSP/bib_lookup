"""
"""

from pathlib import Path

import pytest

import bib_lookup


_CWD = Path(__file__).absolute().parent

(_CWD / "tmp").mkdir(exist_ok=True)

_INPUT_FILE = _CWD / "sample-files" / "invalid_items.bib"

_OUTPUT_FILE = _CWD / "tmp" / "output.bib"


default_bl = bib_lookup.BibLookup(
    output_file=_OUTPUT_FILE, email="someone@gmail.com", ignore_fields="doi"
)
default_bl("10.1088/1361-6579/ac9451")


bl_repr_str = f"""BibLookup(
    align         = 'middle',
    output_file   = {repr(_OUTPUT_FILE)},
    ignore_fields = ['doi']
)"""


def test_checking():
    bl = bib_lookup.BibLookup()
    err_lines = bl.check_bib_file(_INPUT_FILE)
    assert err_lines == [3, 16, 45]


def test_repr():
    assert repr(default_bl) == str(default_bl) == bl_repr_str


def test_warnings():
    with pytest.warns(
        RuntimeWarning,
        match="format `text` is supported only when `arxiv2doi` is True\\. `arxiv2doi` is set to True",
    ):
        bib_lookup.BibLookup(format="text", arxiv2doi=False)
    with pytest.warns(
        RuntimeWarning, match="format `text` is not supported for `pm`, thus ignored"
    ):
        default_bl("PMID: 35344711")
    with pytest.warns(
        RuntimeWarning,
        match="unrecognized `indentifier` \\(none of 'doi', 'pmid', 'pmcid', 'pmurl', 'arxiv'\\)",
    ):
        default_bl("none: xxxxx")
