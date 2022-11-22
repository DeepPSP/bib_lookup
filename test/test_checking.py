from pathlib import Path

import bib_lookup


_CWD = Path(__file__).absolute().parent

_INPUT_FILE = _CWD / "invalid_items.bib"


bl = bib_lookup.BibLookup(
    output_file=_CWD / "output.bib", email="someone@gmail.com", ignore_fields="doi"
)

bl_repr_str = f"""BibLookup(
    align         = 'middle',
    output_file   = {repr(_CWD / "output.bib")},
    ignore_fields = ['doi']
)"""


def test_checking():
    bl = bib_lookup.BibLookup()
    err_lines = bl.check_bib_file(_INPUT_FILE)
    assert err_lines == [3, 16, 45]


def test_repr():
    assert repr(bl) == str(bl) == bl_repr_str
