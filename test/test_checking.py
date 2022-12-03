"""
"""

from pathlib import Path

import pytest

import bib_lookup


_CWD = Path(__file__).resolve().parent

(_CWD / "tmp").mkdir(exist_ok=True)

_INPUT_FILE = _CWD / "sample-files" / "invalid_items.bib"

_LARGE_DATABASE_FILE = _CWD / "sample-files" / "large_database.bib"

_SOURCE_FILE = _CWD / "sample-files" / "sample-source.tex"

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


def test_errors():
    with pytest.raises(
        TypeError,
        match="`identifier` must be a string or a sequence of strings, but got `.+`",
    ):
        default_bl(1)

    with pytest.raises(
        TypeError, match="`index` should be an integer or a string, not `.+`"
    ):
        default_bl[1.0]
    with pytest.raises(AssertionError, match="`.+` not found"):
        default_bl["not-exist"]

    with pytest.raises(FileExistsError, match="Output file \042.+\042 already exists"):
        bib_lookup.BibLookup.simplify_bib_file(
            tex_sources=_SOURCE_FILE,
            bib_file=_LARGE_DATABASE_FILE,
            output_file=_OUTPUT_FILE,
        )

    with pytest.raises(
        AssertionError,
        match="`align` must be one of \\['middle', 'left', 'left-middle', 'left_middle'\\], but got `xxx`",
    ):
        default_bl("10.1088/1361-6579/ac9451", align="xxx")

    with pytest.raises(
        AssertionError,
        match="`output_file` must be a .bib file, but got `.+`",
    ):
        bib_lookup.BibLookup(output_file=_CWD / "tmp" / "output.txt")

    with pytest.raises(
        AssertionError,
        match="`format` must be one of `.+`, but got `.+`",
    ):
        bib_lookup.BibLookup(ignore_fields=1)

    with pytest.raises(
        AssertionError,
        match="`identifier` must be a string or a sequence of strings, but got `.+`",
    ):
        default_bl([1])

    with pytest.raises(
        AssertionError,
        match="`label` must be a sequence of strings of the same length as `identifier`",
    ):
        default_bl(["10.1088/1361-6579/ac9451"], label=["xxx", "yyy"])
    with pytest.raises(
        AssertionError,
        match="`label` must be a sequence of strings of the same length as `identifier`",
    ):
        default_bl(["10.1088/1361-6579/ac9451"], label=[1])
    with pytest.raises(
        AssertionError,
        match="`label` must be a sequence of strings of the same length as `identifier`",
    ):
        default_bl(["10.1088/1361-6579/ac9451"], label="xxx")

    with pytest.raises(AssertionError, match="`output_file` is not specified"):
        bl = bib_lookup.BibLookup()
        bl("10.1088/1361-6579/ac9451")
        bl.save()

    with pytest.raises(
        AssertionError, match="`output_file` must be a .bib file, but got `.+`"
    ):
        default_bl.save(output_file=_CWD / "tmp" / "output.txt")

    with pytest.raises(
        AssertionError,
        match="`identifiers` must be a string \\(or an integer\\) or a sequence of strings \\(or integers\\)",
    ):
        default_bl.save(identifiers=1.2)

    with pytest.raises(
        AssertionError,
        match="`identifiers` must be a string \\(or an integer\\) or a sequence of strings \\(or integers\\)",
    ):
        default_bl.pop(1.2)

    with pytest.raises(AssertionError, match="`bib_file` is not specified"):
        bl = bib_lookup.BibLookup()
        bl.read_bib_file()

    with pytest.raises(
        AssertionError, match="`bib_file` must be a .bib file, but got `.+`"
    ):
        default_bl.read_bib_file(bib_file=_CWD / "tmp" / "output.txt")
