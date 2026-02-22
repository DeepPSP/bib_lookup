import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

import bib_lookup

# Adjust path to import bib_lookup if needed, but it seems installed or in path
# The original test used:
# import bib_lookup

_CWD = Path(__file__).resolve().parent

# Ensure sample files exist or mock them
# The original test assumed they exist.
SAMPLE_DIR = _CWD.parent / "sample-files"
if not SAMPLE_DIR.exists():
    SAMPLE_DIR.mkdir()

# We might need to create dummy sample files if they don't exist
# But let's assume they do based on previous test run logic
# Or better, let's create them in the test setup if missing, to be robust.


def setup_module(module):
    """Create sample files if they don't exist."""
    if not (SAMPLE_DIR / "cache-before-update.csv").exists():
        df = pd.DataFrame({"doi": ["10.1142/s1005386718000305"], "citation": ["@article{...}"]})
        df.to_csv(SAMPLE_DIR / "cache-before-update.csv", index=False)

    if not (SAMPLE_DIR / "cache-after-update.csv").exists():
        df = pd.DataFrame({"doi": ["10.1142/s1005386718000305"], "citation": ["@article{...}"]})
        df.to_csv(SAMPLE_DIR / "cache-after-update.csv", index=False)


def _read_cache_db(db_path):
    conn = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query("SELECT * FROM citations", conn)
    except Exception:
        df = pd.DataFrame(columns=["doi", "citation"])
    conn.close()
    return df


def _write_cache_db(df, db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS citations (
            doi TEXT PRIMARY KEY,
            citation TEXT
        )
    """)
    if not df.empty:
        data = list(df[["doi", "citation"]].itertuples(index=False, name=None))
        conn.executemany("INSERT OR REPLACE INTO citations (doi, citation) VALUES (?, ?)", data)
    conn.commit()
    conn.close()


class SomeClass(bib_lookup.CitationMixin):
    def __init__(self):
        pass

    @property
    def doi(self):
        return "10.1142/s1005386718000305"


class AnotherClass(bib_lookup.CitationMixin):
    def __init__(self):
        pass

    @property
    def doi(self):
        return ["10.1088/1361-6579/ac9451", "10.5281/ZENODO.6435017"]


class YetAnotherClass(bib_lookup.CitationMixin, bib_lookup.utils.ReprMixin):
    def __init__(self):
        pass

    @property
    def doi(self):
        return None


def test_citation_mixin_original(tmp_path, monkeypatch):
    """Restore original test logic with mocks to avoid network calls."""
    db_path = tmp_path / "bib-lookup-cache.db"
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache", db_path)

    # 1. Test lookup=False
    obj = SomeClass()
    citation = obj.get_citation(lookup=False)
    assert citation == "10.1142/s1005386718000305"

    # Test lookup=False with print_result=True
    # Capture stdout
    from io import StringIO

    captured = StringIO()
    sys.stdout = captured
    try:
        res = obj.get_citation(lookup=False, print_result=True)
        assert res is None
        assert "10.1142/s1005386718000305" in captured.getvalue()
    finally:
        sys.stdout = sys.__stdout__

    # 2. Test format != bibtex
    # This should bypass cache logic for retrieval, but still fetch

    # Mock BibLookup to handle format="text"
    class MockBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, doi, format=None, **kwargs):
            if format == "text":
                return "Citation Text"
            return "@article{...}"

    obj._bl = MockBL()

    # Populate cache first to ensure it is IGNORED when format is different
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS citations (doi TEXT PRIMARY KEY, citation TEXT)")
    conn.execute("INSERT INTO citations (doi, citation) VALUES (?, ?)", ("10.1142/s1005386718000305", "@article{cached...}"))
    conn.commit()
    conn.close()

    # Request with format="text"
    res = obj.get_citation(format="text")
    assert res == "Citation Text"
    # Should NOT return cached value
    assert "@article{cached...}" not in res

    # 3. Test print_result=True with cache hit
    # Request with default format (should hit cache)
    captured = StringIO()
    sys.stdout = captured
    try:
        obj.get_citation(print_result=True)
        assert "@article{cached...}" in captured.getvalue()
    finally:
        sys.stdout = sys.__stdout__


def test_citation_mixin_migration(monkeypatch, tmp_path):
    """Test CSV to SQLite migration."""
    # Use a temporary directory for cache to avoid messing with real files

    # Monkeypatch CACHE_DIR in citation_mixin
    # But CACHE_DIR is imported in the module. We need to patch the class attributes.

    csv_path = tmp_path / "bib-lookup-cache.csv"
    db_path = tmp_path / "bib-lookup-cache.db"

    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_csv", csv_path)
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache", db_path)

    # Create dummy CSV
    df = pd.DataFrame({"doi": ["10.123/test"], "citation": ["@article{test, ...}"]})
    df.to_csv(csv_path, index=False)

    # Trigger migration
    obj = SomeClass()
    obj._init_db()

    # Verify DB exists and has data
    assert db_path.exists()
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT citation FROM citations WHERE doi='10.123/test'")
    row = cursor.fetchone()
    assert row is not None
    assert row[0] == "@article{test, ...}"
    conn.close()

    # Verify CSV is gone
    assert not csv_path.exists()


def test_citation_mixin_migration_failure(monkeypatch, tmp_path, capsys):
    """Test CSV migration failure handling."""
    csv_path = tmp_path / "bib-lookup-cache.csv"
    db_path = tmp_path / "bib-lookup-cache.db"

    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_csv", csv_path)
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)

    # Create invalid CSV file
    csv_path.touch()

    # Monkeypatch pd.read_csv to raise Exception
    def mock_read_csv(*args, **kwargs):
        raise ValueError("Simulated read error")

    monkeypatch.setattr(pd, "read_csv", mock_read_csv)

    obj = SomeClass()
    with pytest.warns(UserWarning, match="Failed to migrate CSV cache"):
        obj._init_db()

    captured = capsys.readouterr()
    assert "Failed to migrate CSV cache" not in captured.out


def test_citation_mixin_exceptions(monkeypatch, capsys, tmp_path):
    """Test exception handling in get_citation and update_cache."""
    db_path = tmp_path / "bib-lookup-cache.db"
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)

    obj = SomeClass()

    # Mock BibLookup to raise exception
    # BibLookup is instantiated as class attribute _bl

    # We mock the __call__ method of the instance attached to the class
    # or better, replace the _bl object on the instance.

    class MockBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, *args, **kwargs):
            raise RuntimeError("Simulated lookup error")

    obj._bl = MockBL()

    # Should not crash, but print error
    obj.get_citation(print_result=True)
    captured = capsys.readouterr()
    assert "Failed to lookup citation" in captured.out

    # update_cache should also handle exception
    obj.update_cache(doi="10.123/fail")
    captured = capsys.readouterr()
    assert "Failed to lookup citation" in captured.out

    obj.update_cache(doi=None)


def test_citation_mixin_append_logic(monkeypatch, tmp_path):
    """Test appending new citations to existing ones."""
    db_path = tmp_path / "bib-lookup-cache.db"
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)

    # Pre-populate DB with one DOI
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE IF NOT EXISTS citations (doi TEXT PRIMARY KEY, citation TEXT)")
    conn.execute("INSERT INTO citations (doi, citation) VALUES (?, ?)", ("10.1142/s1005386718000305", "@article{existing...}"))
    conn.commit()
    conn.close()

    class MixedClass(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return ["10.1142/s1005386718000305", "10.1088/new_doi"]

    obj = MixedClass()

    # Mock BibLookup
    class MockBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, doi, **kwargs):
            if doi == "10.1088/new_doi":
                return "@article{new...}"
            return "Error"

    obj._bl = MockBL()

    res = obj.get_citation()
    # Should contain both
    assert "@article{existing...}" in res
    assert "@article{new...}" in res


def test_update_cache_sequence(monkeypatch, tmp_path):
    """Test update_cache with tuple/list."""
    db_path = tmp_path / "bib-lookup-cache.db"
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)

    obj = SomeClass()

    # Mock BibLookup
    class MockBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, doi, **kwargs):
            return f"@article{{citation_{doi}}}"

    obj._bl = MockBL()

    # Pass tuple
    obj.update_cache(doi=("10.1/a", "10.1/b"))

    # Check DB
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM citations")
    count = cursor.fetchone()[0]
    conn.close()


def test_citation_mixin_coverage_gaps(monkeypatch, tmp_path, capsys):
    """Cover specific lines identified as missing coverage."""
    db_path = tmp_path / "bib-lookup-cache.db"
    monkeypatch.setattr(bib_lookup.CitationMixin, "citation_cache_db", db_path)

    # 1. Test empty DOI
    class EmptyDOIClass(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return []

    obj_empty = EmptyDOIClass()
    # It returns "" if print_result is False
    assert obj_empty.get_citation() == ""

    # Test empty DOI with print_result=True
    obj_empty.get_citation(print_result=True)
    captured = capsys.readouterr()
    assert captured.out == ""

    # 2. Test print_result=True with successful lookup
    class SingleDOIClass(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return "10.123/single"

    obj2 = SingleDOIClass()

    class MockBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, doi, **kwargs):
            return "@article{found}"

    obj2._bl = MockBL()

    obj2.get_citation(print_result=True)
    captured = capsys.readouterr()
    assert "@article{found}" in captured.out

    # 3. Test lookup failed warning + print
    # Triggered when citation is empty string at the end

    class FailClass(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return "10.123/fail"

    obj3 = FailClass()

    class FailBL:
        format = "bibtex"
        lookup_errors = ["Error"]

        def clear_cache(self):
            pass

        def __call__(self, doi, **kwargs):
            return "Error"

    obj3._bl = FailBL()

    # We expect print output, so we need to capture it
    # AND we expect a warning
    with pytest.warns(RuntimeWarning, match="Lookup failed"):
        res = obj3.get_citation(print_result=True)
        assert res is None  # print_result=True returns None

    captured = capsys.readouterr()
    # Should print the DOI as fallback
    assert "10.123/fail" in captured.out

    # 4. update_cache exception

    obj4 = FailClass()

    # Mock to raise exception
    class ExceptionBL:
        format = "bibtex"
        lookup_errors = []

        def clear_cache(self):
            pass

        def __call__(self, *args, **kwargs):
            raise RuntimeError("Update Failed")

    obj4._bl = ExceptionBL()

    # Verify exception printing in update_cache
    obj4.update_cache(doi="10.123/fail")
    captured = capsys.readouterr()
    assert "Failed to lookup citation" in captured.out

    # 5. Empty DOI check
    # The current implementation returns None if print_result=True and doi is empty, and "" if print_result=False

    class TrulyEmpty(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return []

    obj5 = TrulyEmpty()
    res = obj5.get_citation(print_result=True)
    assert res is None

    res = obj5.get_citation(print_result=False)
    assert res == ""

    obj6 = AnotherClass()
    res = obj6.get_citation()
    assert "10.1088/1361-6579/ac9451" in res
    assert "10.5281/ZENODO.6435017" in res

    obj7 = YetAnotherClass()
    res = obj7.get_citation()
    assert res == ""
