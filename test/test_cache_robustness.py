"""Regression tests for citation-cache robustness (bug report 2026-11-13).

Covers:
1. import must not crash (nor create dirs) with an unusable HOME;
2. BIB_LOOKUP_CACHE_DIR / 3. XDG_CACHE_HOME env overrides;
4. a valid database on a read-only filesystem is never deleted;
5. a corrupt database is quarantined (renamed aside), never lost;
6. a locked database is never deleted;
7. no unclosed SQLite connections (ResourceWarning-free);
8. concurrent initialization across processes must not race.
"""

import os
import sqlite3
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

import bib_lookup
from bib_lookup import _const
from bib_lookup import citation_mixin as cm

RUNS_AS_ROOT = hasattr(os, "geteuid") and os.geteuid() == 0
IS_POSIX = os.name == "posix"


@pytest.fixture(autouse=True)
def _reset_global_cache_state():
    cm._reset_cache_disable_state()
    yield
    cm._reset_cache_disable_state()


class _Holder(bib_lookup.CitationMixin):
    def __init__(self, doi="10.1234/holder"):
        self._doi = doi

    @property
    def doi(self):
        return self._doi


class _MockBL:
    """Offline BibLookup stand-in: canned bibtex, no network."""

    format = "bibtex"
    lookup_errors = ("__error__",)

    def clear_cache(self):
        pass

    def __call__(self, doi, **kwargs):
        return f"@article{{{doi}}}"


def _patch_cache_paths(monkeypatch, tmp_path):
    db = tmp_path / "bib-lookup-cache.db"
    csv = tmp_path / "bib-lookup-cache.csv"
    monkeypatch.setattr(cm.CitationMixin, "citation_cache_db", db)
    monkeypatch.setattr(cm.CitationMixin, "citation_cache_csv", csv)
    monkeypatch.setattr(cm.CitationMixin, "citation_cache", db)
    return db, csv


def _run_py(code: str, env: dict = None, timeout: int = 180):
    full_env = {**os.environ, **(env or {})}
    # The child's HOME may be overridden, which would move its user-site
    # directory along with it; pin PYTHONUSERBASE to the parent's real user
    # base so bib_lookup and its dependencies stay importable regardless of
    # HOME.  (Do NOT use PYTHONPATH for this: site dirs on PYTHONPATH shadow
    # the stdlib, e.g. a legacy `dataclasses` backport breaks Python 3.13.)
    import site as _site

    full_env.setdefault("PYTHONUSERBASE", _site.getuserbase())
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(code)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=full_env,
    )


# ----------------------------------------------------------------------
# 1. unusable HOME must not break the import (nor touch the filesystem)
# ----------------------------------------------------------------------

@pytest.mark.skipif(not IS_POSIX, reason="/proc and chmod semantics are POSIX")
def test_import_never_crashes_with_unusable_home(tmp_path):
    unwritable = tmp_path / "home"
    unwritable.mkdir()
    unwritable.chmod(0o500)
    env = {"HOME": str(unwritable), "BIB_LOOKUP_CACHE_DIR": "", "XDG_CACHE_HOME": ""}
    r = _run_py("import bib_lookup; print('IMPORT-OK')", env)
    unwritable.chmod(0o755)
    assert r.returncode == 0, r.stderr
    assert "IMPORT-OK" in r.stdout
    # import must not have created anything inside the unwritable HOME
    assert not (unwritable / ".cache").exists()


@pytest.mark.skipif(not IS_POSIX or not Path("/proc").is_dir(), reason="needs /proc")
def test_import_with_nonexistent_home(tmp_path):
    missing = tmp_path / "no-such-home"
    r = _run_py("import bib_lookup; print('IMPORT-OK')", {"HOME": str(missing)})
    assert r.returncode == 0, r.stderr
    assert "IMPORT-OK" in r.stdout
    assert not missing.exists()


# ----------------------------------------------------------------------
# 2. BIB_LOOKUP_CACHE_DIR override
# ----------------------------------------------------------------------

def test_bib_lookup_cache_dir_env_override(tmp_path):
    target = tmp_path / "custom-cache"
    env = {"BIB_LOOKUP_CACHE_DIR": str(target), "HOME": "/proc", "XDG_CACHE_HOME": ""}
    code = """
        import os
        from pathlib import Path
        import bib_lookup

        from bib_lookup._const import get_cache_dir

        d = get_cache_dir()
        assert d == Path(os.environ["BIB_LOOKUP_CACHE_DIR"]), d

        class H(bib_lookup.CitationMixin):
            @property
            def doi(self):
                return "10.1/env"

        h = H()
        assert h._init_db() is True
        assert (d / "bib-lookup-cache.db").exists()
        print("ENV-OK")
    """
    r = _run_py(code, env)
    assert r.returncode == 0, r.stderr
    assert "ENV-OK" in r.stdout
    assert target.is_dir()


def test_resolution_order(monkeypatch, tmp_path):
    custom, xdg = tmp_path / "c1", tmp_path / "xdg"
    monkeypatch.setenv("BIB_LOOKUP_CACHE_DIR", str(custom))
    assert _const._resolve_cache_dir()[0] == custom
    monkeypatch.delenv("BIB_LOOKUP_CACHE_DIR")
    monkeypatch.setenv("XDG_CACHE_HOME", str(xdg))
    assert _const._resolve_cache_dir()[0] == xdg / "bib-lookup"
    monkeypatch.delenv("XDG_CACHE_HOME")
    assert _const._resolve_cache_dir()[0] == _const.CACHE_DIR


@pytest.mark.skipif(RUNS_AS_ROOT, reason="chmod is ineffective for root")
def test_resolution_falls_back_to_temp_when_home_unwritable(monkeypatch, tmp_path):
    import tempfile

    home = tmp_path / "home"
    (home / ".cache").mkdir(parents=True)
    (home / ".cache").chmod(0o500)  # make the cache root's parent unwritable
    monkeypatch.setattr(_const, "CACHE_DIR", home / ".cache" / "bib-lookup")
    try:
        resolved, is_temporary = _const._resolve_cache_dir()
        assert is_temporary
        assert resolved is not None
        assert str(resolved).startswith(tempfile.gettempdir())
    finally:
        (home / ".cache").chmod(0o755)


# ----------------------------------------------------------------------
# 3. XDG_CACHE_HOME override
# ----------------------------------------------------------------------

@pytest.mark.skipif(not IS_POSIX, reason="needs /proc")
def test_xdg_cache_home_env(tmp_path):
    xdg = tmp_path / "xdgroot"
    r = _run_py(
        """
        import bib_lookup
        from bib_lookup._const import get_cache_dir
        print("XDG-OK", get_cache_dir())
    """,
        {"XDG_CACHE_HOME": str(xdg), "HOME": "/proc"},
    )
    assert r.returncode == 0, r.stderr
    assert (xdg / "bib-lookup").is_dir()


# ----------------------------------------------------------------------
# 4. valid database on a read-only filesystem: never deleted, never crashes
# ----------------------------------------------------------------------

@pytest.mark.skipif(RUNS_AS_ROOT, reason="chmod is ineffective for root")
def test_valid_db_on_readonly_dir_survives(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE citations (doi TEXT PRIMARY KEY, citation TEXT)")
        conn.execute("INSERT INTO citations VALUES ('10.1/precious', '@article{precious}')")
        conn.commit()
    finally:
        conn.close()

    monkeypatch.setattr(cm, "SQLITE_TIMEOUT_S", 0.2)
    tmp_path.chmod(0o555)
    try:
        holder = _Holder()
        with pytest.warns(RuntimeWarning, match="disabled"):
            assert holder._init_db() is False
    finally:
        tmp_path.chmod(0o755)

    # the valid database must be untouched
    assert db.exists()
    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT citation FROM citations WHERE doi='10.1/precious'").fetchall()
    finally:
        conn.close()
    assert rows == [("@article{precious}",)]


# ----------------------------------------------------------------------
# 5. corrupt database: quarantined (renamed aside), never lost
# ----------------------------------------------------------------------

def test_corrupt_db_quarantined_not_deleted(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    garbage = b"definitely not a sqlite database" * 10
    db.write_bytes(garbage)

    holder = _Holder()
    with pytest.warns(UserWarning, match="corrupt"):
        assert holder._init_db() is True

    quarantined = list(tmp_path.glob("*.corrupt-*"))
    assert len(quarantined) == 1, "corrupt file must be moved aside"
    assert quarantined[0].read_bytes() == garbage, "original bytes must be recoverable"
    assert db.exists(), "a fresh database must be in place"

    conn = sqlite3.connect(db)
    try:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name='citations'").fetchone() is not None
    finally:
        conn.close()


# ----------------------------------------------------------------------
# 6. locked database: never deleted
# ----------------------------------------------------------------------

@pytest.mark.skipif(not IS_POSIX, reason="POSIX file locking semantics")
def test_locked_db_is_never_deleted(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    conn = sqlite3.connect(db)
    try:
        conn.execute("CREATE TABLE citations (doi TEXT PRIMARY KEY, citation TEXT)")
        conn.execute("INSERT INTO citations VALUES ('10.1/keep', '@article{keep}')")
        conn.commit()
    finally:
        conn.close()

    holder_code = textwrap.dedent("""
        import sqlite3, sys, time
        conn = sqlite3.connect(sys.argv[1], timeout=5.0)
        conn.execute("BEGIN EXCLUSIVE")
        print("LOCKED", flush=True)
        time.sleep(30)
    """)
    proc = subprocess.Popen(
        [sys.executable, "-c", holder_code, str(db)], stdout=subprocess.PIPE, text=True
    )
    try:
        assert proc.stdout.readline().strip() == "LOCKED"
        monkeypatch.setattr(cm, "SQLITE_TIMEOUT_S", 0.2)
        holder = _Holder()
        with pytest.warns(RuntimeWarning, match="disabled"):
            assert holder._init_db() is False
        assert db.exists(), "a locked database must never be deleted"
    finally:
        proc.kill()
        proc.wait()

    conn = sqlite3.connect(db)
    try:
        rows = conn.execute("SELECT citation FROM citations WHERE doi='10.1/keep'").fetchall()
    finally:
        conn.close()
    assert rows == [("@article{keep}",)], "locked database rows must survive"


# ----------------------------------------------------------------------
# 7. no unclosed SQLite connections anywhere in the cache paths
# ----------------------------------------------------------------------

def test_no_unclosed_sqlite_connections(tmp_path):
    env = {
        "BIB_LOOKUP_CACHE_DIR": str(tmp_path / "cache"),
        "PYTHONWARNINGS": "always::ResourceWarning",
    }
    code = """
        import gc
        import bib_lookup

        class BL:
            format = "bibtex"
            lookup_errors = ("__error__",)
            def clear_cache(self): pass
            def __call__(self, doi, **kw): return f"@article{{{doi}}}"

        class H(bib_lookup.CitationMixin):
            @property
            def doi(self): return "10.1/rw"

        h = H()
        assert h._init_db() is True
        h._bl = BL()
        h.get_citation()   # cache miss -> mock fetch -> write-back
        h.get_citation()   # cache hit
        h.update_cache(doi="10.1/rw2")
        h._check_db_file()  # probe path
        gc.collect()
        print("RW-CHECK-DONE")
    """
    r = _run_py(code, env)
    assert r.returncode == 0, r.stderr
    assert "RW-CHECK-DONE" in r.stdout
    assert "unclosed database" not in r.stderr, r.stderr


# ----------------------------------------------------------------------
# 8. concurrent initialization across processes
# ----------------------------------------------------------------------

def test_concurrent_init_no_races(tmp_path):
    env = {"BIB_LOOKUP_CACHE_DIR": str(tmp_path / "shared")}
    code = """
        import os
        import bib_lookup

        class BL:
            format = "bibtex"
            lookup_errors = ("__error__",)
            def clear_cache(self): pass
            def __call__(self, doi, **kw): return f"@article{{{doi}}}"

        class H(bib_lookup.CitationMixin):
            @property
            def doi(self): return f"10.1999/pid-{os.getpid()}"

        h = H()
        h._bl = BL()
        mine = f"10.1999/pid-{os.getpid()}"
        assert h.get_citation() == f"@article{{{mine}}}"
        print(f"PID-OK {os.getpid()}")
    """
    procs = [subprocess.Popen([sys.executable, "-c", textwrap.dedent(code)], env={**os.environ, **env},
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(4)]
    outs = [p.communicate(timeout=180) for p in procs]
    for p, (out, err) in zip(procs, outs):
        assert p.returncode == 0, f"stderr: {err}"
        assert "PID-OK" in out

    db = tmp_path / "shared" / "bib-lookup-cache.db"
    assert db.exists()
    conn = sqlite3.connect(db)
    try:
        dois = {row[0] for row in conn.execute("SELECT doi FROM citations").fetchall()}
    finally:
        conn.close()
    expected = set()
    for out, _ in outs:
        for line in out.splitlines():
            if line.startswith("PID-OK"):
                expected.add(f"10.1999/pid-{line.split()[1]}")
    assert expected <= dois, f"lost rows: {expected - dois}"
