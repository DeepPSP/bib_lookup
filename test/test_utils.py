""" """

import random
from pathlib import Path

import pytest

from bib_lookup.utils import capitalize_title, color_text, gather_tex_source_files_in_one, md_text, printmd, str2bool

_SAMPLE_DIR = Path(__file__).resolve().parents[1] / "sample-files"

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
    ct = color_text("test", color=("red", "green", "blue"))

    with pytest.raises(TypeError, match="Cannot color text with provided color of type `.+`"):
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


def test_str2bool():
    for s in ("yes", "true", "t", "y", "1", "True", "Yes"):
        assert str2bool(s) is True
        assert str2bool(s.upper()) is True
    for s in ("no", "false", "f", "n", "0", "False", "No"):
        assert str2bool(s) is False
        assert str2bool(s.upper()) is False
    for s in (1, 1.2):
        assert str2bool(s) is True
    for s in (0, 0.0):
        assert str2bool(s) is False
    assert str2bool(True) is True
    assert str2bool(False) is False
    with pytest.raises(ValueError, match="Boolean value expected"):
        str2bool("foo")


def test_gather_tex_source_files_in_one():
    entry_file = _SAMPLE_DIR / "sample-source.tex"
    ret = gather_tex_source_files_in_one(entry_file)
    assert ret.splitlines()[0] == entry_file.read_text().splitlines()[0]

    output_file = _TMP_DIR / "sample-source-in-one.tex"
    if output_file.exists():
        output_file.unlink()
    ret = gather_tex_source_files_in_one(entry_file, write_file=True, output_file=output_file)
    assert ret == str(output_file)
    assert output_file.is_file()
    assert output_file.read_text().splitlines()[0] == entry_file.read_text().splitlines()[0]

    default_output_file = entry_file.parent / f"{entry_file.stem}_in_one.tex"
    assert not default_output_file.exists()
    ret = gather_tex_source_files_in_one(entry_file, write_file=True)
    assert ret == str(default_output_file)
    assert default_output_file.is_file()
    assert default_output_file.read_text().splitlines()[0] == entry_file.read_text().splitlines()[0]
    default_output_file.unlink()
    del default_output_file

    with pytest.raises(
        ValueError,
        match=("The entry file and the output file are the same, which is not allowed for security reasons."),
    ):
        gather_tex_source_files_in_one(entry_file, write_file=True, output_file=entry_file)

    with pytest.raises(
        FileExistsError,
        match=(
            "The output file exists. If you want to overwrite it, "
            "you should delete it manually first. Or set `overwrite=True`."
        ),
    ):
        gather_tex_source_files_in_one(entry_file, write_file=True, output_file=output_file)

    gather_tex_source_files_in_one(entry_file, write_file=True, output_file=output_file, overwrite=True)


def test_capitalize_title():
    test_title_1 = """"Why Should I Trust You?": Explaining the Predictions of Any Classifier"""
    test_title_2 = """Modelling the Effect of Exercise on Insulin Pharmacokinetics in "Continuous Subcutaneous Insulin Infusion" Treated Type 1 Diabetes Patients"""
    # it is "ProxSkip" in the original title, but we are not able to treat the acronyms
    test_title_3 = """Proxskip: Yes! Local Gradient Steps Provably Lead to Communication Acceleration! Finally!"""

    def random_case_title(title):
        return "".join([c.upper() if random.random() > 0.5 else c.lower() for c in title])

    for _ in range(100):
        title = random_case_title(test_title_1)
        assert capitalize_title(title) == test_title_1, f"Failed for {test_title_1}\ngot {capitalize_title(title)}"
        title = random_case_title(test_title_2)
        assert capitalize_title(title) == test_title_2, f"Failed for {test_title_2}\ngot {capitalize_title(title)}"
        title = random_case_title(test_title_3)
        assert capitalize_title(title) == test_title_3, f"Failed for {test_title_3}\ngot {capitalize_title(title)}"
