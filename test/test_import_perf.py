"""Tests that `import bib_lookup` stays lightweight.

Heavy optional-path dependencies (pandas, pybtex and its pkg_resources,
IPython) must not be loaded at import time; pybtex should load only when
citation styles are actually accessed, pandas only when the citation cache
is actually used.

The checks run in a subprocess so that the importing test session (which
may have these modules loaded for other tests) does not pollute
`sys.modules`.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[1]

_CLEAN_IMPORT_SCRIPT = """\
import sys
import bib_lookup  # noqa: F401

heavy = ("pandas", "pybtex", "pkg_resources", "IPython")
loaded = sorted({h for m in sys.modules for h in heavy if m == h or m.startswith(h + ".")})
assert not loaded, f"heavy modules loaded on import: {loaded}"
print("ok")
"""

_LAZY_STYLES_SCRIPT = """\
import sys
import bib_lookup
from bib_lookup import bib_lookuper

assert "pybtex" not in sys.modules, "pybtex loaded before styles access"
styles = bib_lookuper.supported_styles
for key in ("gbt7714", "gbt", "gbt-7714", "ieee", "apa", "chicago", "unsrt", "plain", "alpha"):
    assert key in styles, f"missing style {key}"
assert any(m == "pybtex" or m.startswith("pybtex.") for m in sys.modules), (
    "pybtex should be loaded after `supported_styles` access"
)
print("ok")
"""


def _run_in_subprocess(script: str) -> None:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    res = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(REPO_ROOT),
        timeout=120,
    )
    assert res.returncode == 0, f"stdout:\n{res.stdout}\nstderr:\n{res.stderr}"
    assert res.stdout.strip().endswith("ok")


def test_import_does_not_load_heavy_modules() -> None:
    _run_in_subprocess(_CLEAN_IMPORT_SCRIPT)


def test_supported_styles_discovered_lazily() -> None:
    _run_in_subprocess(_LAZY_STYLES_SCRIPT)


def test_bib_entry_required_fields_dict() -> None:
    # Replacement for the removed `DF_BIB_ENTRY_TYPES` DataFrame: the dict
    # covers the classic BibTeX types (a subset of `BIB_ENTRY_TYPES`);
    # biblatex-only types like "software" simply have no required fields,
    # same as with the old DataFrame lookup.
    from bib_lookup._bib import BIB_ENTRY_REQUIRED_FIELDS, BIB_ENTRY_TYPES

    assert set(BIB_ENTRY_REQUIRED_FIELDS) <= set(BIB_ENTRY_TYPES)
    assert all(isinstance(v, list) for v in BIB_ENTRY_REQUIRED_FIELDS.values())
    assert BIB_ENTRY_REQUIRED_FIELDS["article"] == ["author", "title", "journal", "year|date"]
    assert BIB_ENTRY_REQUIRED_FIELDS["misc"] == []


def test_check_required_fields_biblatex_only_type() -> None:
    # "software" is a valid entry type but has no required-fields entry;
    # the check must pass silently (as it did with the DataFrame lookup).
    from collections import OrderedDict

    from bib_lookup._bib import BibItem

    bi = BibItem("10.1234/test", "software", OrderedDict([("title", "T")]), check_fields=False)
    bi.check_required_fields()


@pytest.mark.parametrize(
    "entry_type, fields, expect_ok",
    [
        ("article", {"author": "A", "title": "T", "journal": "J", "year": "2020"}, True),
        ("article", {"author": "A", "title": "T", "year": "2020"}, False),  # journal missing
        ("misc", {}, True),
    ],
)
def test_check_required_fields_via_dict(entry_type: str, fields: dict, expect_ok: bool) -> None:
    from collections import OrderedDict

    from bib_lookup._bib import BibItem

    bi = BibItem("10.1234/test", entry_type, OrderedDict(fields), check_fields=False)
    if expect_ok:
        bi.check_required_fields()
    else:
        with pytest.raises(AssertionError):
            bi.check_required_fields()
