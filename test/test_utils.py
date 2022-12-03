"""
"""

from pathlib import Path

import pytest

from bib_lookup.utils import (
    color_text,
    md_text,
    printmd,
    gather_tex_source_files_in_one,
)


_SAMPLE_DIR = Path(__file__).resolve().parent / "sample-files"

_TMP_DIR = Path(__file__).resolve().parents[1] / "tmp"
_TMP_DIR.mkdir(exist_ok=True)


def test_color_text():
    ct = color_text("test", method="html")
    ct = color_text("test", method="file")
    for color in [
        "green",
        "red",
        "blue",
        "purple",
        "gray",
        "bold",
        "underline",
        "warning",
    ]:
        ct = color_text("test", color=color)
        ct = color_text("test", color=color, method="html")
        ct = color_text("test", color=color, method="file")

    with pytest.raises(
        TypeError, match="Cannot color text with provided color of type `.+`"
    ):
        ct = color_text("test", color=1)

    with pytest.raises(ValueError, match="unknown text color `xxx`"):
        ct = color_text("test", color="xxx")

    with pytest.raises(ValueError, match="unknown text color method `xxx`"):
        ct = color_text("test", color="red", method="xxx")


def test_md_text():
    md_text("test")
    md_text("test", color="green")
    md_text("test", color=("red", "green", "blue"))
    md_text("test", color="red", method="html")
    md_text("test", color="yellow", bold=True)
    md_text("test", color="blue", font_size=20)
    md_text("test", color="purple", font_family="monospace")

    with pytest.raises(AssertionError, match="unknown method `xxx`"):
        md_text("test", color="red", method="xxx")


def test_printmd():
    text = md_text("test")
    printmd(text)
    text = md_text("test", color="green")
    printmd(text)
    text = md_text("test", color="red", method="html")
    printmd(text)
    text = md_text("test", color="yellow", bold=True)
    printmd(text)
    text = md_text("test", color="blue", font_size=20)
    printmd(text)
    text = md_text("test", color="purple", font_family="monospace")
    printmd(text)


def test_gather_tex_source_files_in_one():
    entry_file = _SAMPLE_DIR / "sample-source.tex"
    ret = gather_tex_source_files_in_one(entry_file)
    assert ret.splitlines()[0] == entry_file.read_text().splitlines()[0]

    output_file = _TMP_DIR / "sample-source-in-one.tex"
    if output_file.exists():
        output_file.unlink()
    ret = gather_tex_source_files_in_one(
        entry_file, write_file=True, output_file=output_file
    )
    assert ret == str(output_file)
    assert output_file.is_file()
    assert (
        output_file.read_text().splitlines()[0]
        == entry_file.read_text().splitlines()[0]
    )

    with pytest.raises(
        ValueError,
        match=(
            "The entry file and the output file are the same, "
            "which is not allowed for security reasons."
        ),
    ):
        gather_tex_source_files_in_one(
            entry_file, write_file=True, output_file=entry_file
        )

    with pytest.raises(
        ValueError,
        match=(
            "The output file exists. "
            "If you want to overwrite it, you should delete it manually first."
        ),
    ):
        gather_tex_source_files_in_one(
            entry_file, write_file=True, output_file=output_file
        )
