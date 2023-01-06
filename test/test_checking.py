"""
"""

from pathlib import Path

import pytest

from bib_lookup import BibLookup


_CWD = Path(__file__).resolve().parent

_INPUT_FILE = _CWD.parent / "sample-files" / "invalid_items.bib"

_TMP_DIR = _CWD.parent / "tmp"
_TMP_DIR.mkdir(exist_ok=True)

_OUTPUT_FILE = _TMP_DIR / "test_checking_output.bib"


default_bl = BibLookup(
    output_file=_OUTPUT_FILE, email="someone@gmail.com", ignore_fields="doi"
)
default_bl("10.1088/1361-6579/ac9451")


bl_repr_str = f"""BibLookup(
    align         = 'middle',
    output_file   = {repr(_OUTPUT_FILE)},
    ignore_fields = ['doi']
)"""


def test_checking():
    bl = BibLookup()
    err_lines = bl.check_bib_file(_INPUT_FILE)
    assert err_lines == [3, 16, 45]


def test_repr():
    assert repr(default_bl) == str(default_bl) == bl_repr_str


def test_properties():
    assert isinstance(default_bl.style, str)
    assert isinstance(default_bl.format, str)
    assert isinstance(default_bl.pubmed_pattern, str)
    assert isinstance(default_bl.pubmed_pattern_prefix, str)
    assert isinstance(default_bl.doi_pattern, str)
    assert isinstance(default_bl.doi_pattern_prefix, str)
    assert isinstance(default_bl.arxiv_pattern, str)
    assert isinstance(default_bl.arxiv_pattern_prefix, str)
    assert isinstance(default_bl.bib_header_pattern, str)
    assert isinstance(default_bl.default_err, str)
    assert isinstance(default_bl.network_err, str)
    assert isinstance(default_bl.timeout_err, str)
    assert isinstance(default_bl.lookup_errors, list) and all(
        isinstance(err, str) for err in default_bl.lookup_errors
    )
    assert isinstance(default_bl.ignore_fields, list) and all(
        isinstance(field, str) for field in default_bl.ignore_fields
    )


def test_warnings():
    with pytest.warns(
        RuntimeWarning,
        match="format `text` is supported only when `arxiv2doi` is True\\. `arxiv2doi` is set to True",
    ):
        BibLookup(format="text", arxiv2doi=False)
    with pytest.warns(
        RuntimeWarning, match="format `text` is not supported for `pm`, thus ignored"
    ):
        default_bl("PMID: 35344711", format="text")
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

    # with pytest.raises(
    #     AssertionError,
    #     match="`align` must be one of \\['middle', 'left', 'left-middle', 'left_middle'\\], but got `xxx`",
    # ):
    #     default_bl("10.1088/1361-6579/ac9451", align="xxx")

    with pytest.raises(
        AssertionError,
        match="`output_file` must be a .bib file, but got `.+`",
    ):
        BibLookup(output_file=_TMP_DIR / "output.txt")

    with pytest.raises(
        AssertionError,
        match="`format` must be one of `.+`, but got `.+`",
    ):
        BibLookup(format="xxx")

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
        bl = BibLookup()
        bl("10.1088/1361-6579/ac9451")
        bl.save()

    with pytest.raises(
        AssertionError, match="`output_file` must be a .bib file, but got `.+`"
    ):
        default_bl.save(output_file=_TMP_DIR / "output.txt")

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
        bl = BibLookup()
        bl.read_bib_file()

    with pytest.raises(
        AssertionError, match="`bib_file` must be a .bib file, but got `.+`"
    ):
        default_bl.read_bib_file(bib_file=_TMP_DIR / "output.txt")

    feed_dict = dict(
        entry_type="article",
        label="xxx",
        title="A Novel Deep Learning Package for Electrocardiography Research",
        author="Hao Wen and Jingsu Kang",
        journal="Physiological Measurement",
        year=2022,
        month=11,
        publisher="IOP Publishing",
        volume=43,
        number=11,
        pages=115006,
    )
    default_bl._to_bib_item(
        res=feed_dict,
        identifier="10.1088/1361-6579/ac9451",
        label="xxx",
    )
    with pytest.raises(
        AssertionError,
        match="`label` must be a string",
    ):
        default_bl._to_bib_item(
            res=feed_dict,
            identifier="10.1088/1361-6579/ac9451",
            label=1,
        )

    assert default_bl("none: xxxxx", ignore_errors=True, verbose=5) == ""
