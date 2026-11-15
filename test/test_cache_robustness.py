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
import tempfile
import textwrap
import warnings
from contextlib import contextmanager
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
    _const._CACHE_DIR_RESOLVED = _const._UNSET
    yield
    cm._reset_cache_disable_state()
    _const._CACHE_DIR_RESOLVED = _const._UNSET


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


def _child_env(extra: dict = None) -> dict:
    """Environment for child interpreters spawned by these tests.

    Pins PYTHONUSERBASE to the parent's real user base so the child stays
    importable even when its HOME is overridden (site dirs on PYTHONPATH
    would shadow the stdlib, e.g. a legacy `dataclasses` backport breaking
    Python 3.13), and keeps pytest-cov's subprocess-coverage hooks
    (COV_CORE_* / COVERAGE_*) out: the embedded early-start tracer crashes
    numpy's single-phase-init guard, and child-process execution is out of
    scope for the coverage report by design.
    """
    import site as _site

    env = {**os.environ, **(extra or {})}
    env.setdefault("PYTHONUSERBASE", _site.getuserbase())
    for key in [k for k in env if k.startswith(("COV_CORE_", "COVERAGE_"))]:
        env.pop(key)
    return env


def _run_py(code: str, env: dict = None, timeout: int = 180):
    full_env = _child_env(env)
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


def test_get_cache_dir_memoized_and_created(monkeypatch, tmp_path):
    monkeypatch.setenv("BIB_LOOKUP_CACHE_DIR", str(tmp_path / "memo"))
    d1 = _const.get_cache_dir()
    d2 = _const.get_cache_dir()
    assert d1 == d2 == tmp_path / "memo"
    assert (tmp_path / "memo").is_dir()
    # no warning on the happy path
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _const.get_cache_dir() == d1


# ----------------------------------------------------------------------
# 2b. undeterminable home directory (HOME unset AND no passwd entry):
#     Path.home() itself raises RuntimeError -> import must still succeed
# ----------------------------------------------------------------------


def test_import_with_undeterminable_home(tmp_path):
    code = """
        import pathlib
        import tempfile

        def _raise():
            raise RuntimeError("Could not determine home directory")

        pathlib.Path.home = staticmethod(_raise)

        import bib_lookup
        from bib_lookup._const import CONFIG_FILE, DEFAULT_CITATION_CACHE_DB, get_cache_dir

        assert CONFIG_FILE is None
        assert DEFAULT_CITATION_CACHE_DB is None

        bib_lookup.BibLookup()  # config read is guarded against None

        d = get_cache_dir()
        assert d is not None and str(d).startswith(tempfile.gettempdir())

        class H(bib_lookup.CitationMixin):
            @property
            def doi(self):
                return "10.1/nohome"

        h = H()
        assert h._init_db() is True  # temp-fallback caching still works
        print("NOHOME-OK")
    """
    r = _run_py(code, {"HOME": ""})
    assert r.returncode == 0, r.stderr
    assert "NOHOME-OK" in r.stdout


def test_safe_home_and_resolution_without_home(monkeypatch, tmp_path):
    import pathlib

    def _raise():
        raise RuntimeError("Could not determine home directory")

    monkeypatch.setattr(pathlib.Path, "home", staticmethod(_raise))
    assert _const._safe_home() is None

    # with CACHE_DIR undeterminable, the chain still works: env -> temp
    monkeypatch.setattr(_const, "CACHE_DIR", None)
    monkeypatch.delenv("BIB_LOOKUP_CACHE_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    resolved, is_temporary = _const._resolve_cache_dir()
    assert is_temporary and resolved is not None

    monkeypatch.setenv("BIB_LOOKUP_CACHE_DIR", str(tmp_path / "envroot"))
    resolved, is_temporary = _const._resolve_cache_dir()
    assert resolved == tmp_path / "envroot" and not is_temporary


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
    proc = subprocess.Popen([sys.executable, "-c", holder_code, str(db)], stdout=subprocess.PIPE, text=True)
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
    procs = [
        subprocess.Popen(
            [sys.executable, "-c", textwrap.dedent(code)],
            env=_child_env(env),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for _ in range(4)
    ]
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


# ======================================================================
# In-process twins: exercise the branches that are otherwise only hit
# inside the subprocess tests above, so they count for coverage.
# ======================================================================


def _mock_bl(return_map=None, default="@article{{{doi}}}"):
    class BL:
        format = "bibtex"
        lookup_errors = ("__error__",)

        def clear_cache(self):
            pass

        def __call__(self, doi, **kwargs):
            if return_map and doi in return_map:
                return return_map[doi]
            return default.format(doi=doi)

    return BL()


def test_default_path_roundtrip_and_update_cache(monkeypatch, tmp_path):
    """Full lifecycle through the REAL (non-overridden) cache paths."""
    root = tmp_path / "envroot"
    monkeypatch.setenv("BIB_LOOKUP_CACHE_DIR", str(root))

    class H(bib_lookup.CitationMixin):
        @property
        def doi(self):
            return ["10.1/a", "10.1/b"]

    h = H()
    h._bl = _mock_bl()
    res = h.get_citation()  # cache miss -> mock fetch -> write-back
    assert "@article{10.1/a}" in res and "@article{10.1/b}" in res
    db = root / "bib-lookup-cache.db"
    assert db.exists()

    h2 = H()  # fresh instance, same default resolution: cache hit
    h2._bl = _mock_bl(default="SHOULD-NOT-BE-USED")
    res2 = h2.get_citation()
    assert "@article{10.1/a}" in res2 and "SHOULD-NOT-BE-USED" not in res2

    h2.update_cache()  # doi=None: lists everything, refreshes, writes back
    conn = sqlite3.connect(db)
    try:
        dois = {row[0] for row in conn.execute("SELECT doi FROM citations")}
    finally:
        conn.close()
    assert {"10.1/a", "10.1/b"} <= dois


def test_resolve_cache_default_root_none(monkeypatch):
    monkeypatch.setattr(cm, "get_cache_dir", lambda: None)
    h = _Holder()
    assert h._resolve_cache() is False
    assert h.citation_cache_db is None and h.citation_cache_csv is None
    assert h._cache_enabled is False


def test_resolve_cache_with_none_override(monkeypatch):
    monkeypatch.setattr(cm.CitationMixin, "citation_cache_db", None)
    h = _Holder()
    assert h._resolve_cache() is False
    assert h._cache_enabled is False


def test_resolve_cache_mkdir_oserror(monkeypatch, tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file")
    db = blocker / "sub" / "bib-lookup-cache.db"
    monkeypatch.setattr(cm.CitationMixin, "citation_cache_db", db)
    monkeypatch.setattr(cm.CitationMixin, "citation_cache_csv", blocker / "sub" / "c.csv")
    h = _Holder()
    with pytest.warns(RuntimeWarning, match="disabled"):
        assert h._resolve_cache() is False


def test_global_disable_short_circuits_resolve_and_init(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)
    holder = _Holder()
    holder._disable_cache("test")
    other = _Holder()
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # no second warning: warn-once contract
        assert other._init_db() is False  # silent early-return via _CACHE_DISABLED
        other.update_cache(doi="10.1/whatever")  # same silent early-return


def test_init_lock_without_fcntl(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm, "fcntl", None)
    h = _Holder()
    assert h._init_db() is True  # lock skipped entirely, cache still created
    assert db.exists()


def _failing_fcntl():
    class F:
        LOCK_EX = 2
        LOCK_UN = 8

        @staticmethod
        def flock(fh, op):
            raise OSError("synthetic: fs refuses locks")

    return F()


def test_init_lock_open_oserror_with_usable_cache(monkeypatch, tmp_path):
    """Exotic filesystem refuses opening the lock file but allows the cache:
    initialization proceeds unlocked and completes normally."""
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    real_open = open

    def guarded_open(file, mode="r", *a, **kw):
        if "init-lock" in str(file):
            raise PermissionError(f"synthetic: lock refused on {file}")
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr("builtins.open", guarded_open)
    h = _Holder()
    assert h._init_db() is True
    assert db.exists()


def test_init_lock_flock_oserror_is_best_effort(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm, "fcntl", _failing_fcntl())
    h = _Holder()
    assert h._init_db() is True
    assert db.exists()


def test_init_lock_open_oserror_readonly_dir(monkeypatch, tmp_path):
    if RUNS_AS_ROOT:
        pytest.skip("chmod is ineffective for root")
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    tmp_path.chmod(0o555)
    try:
        h = _Holder()
        with pytest.warns(RuntimeWarning, match="disabled"):
            assert h._init_db() is False  # schema creation fails on readonly fs
    finally:
        tmp_path.chmod(0o755)


def _scripted_connect(script):
    """Replace sqlite3.connect (as seen from citation_mixin) with a scripted one."""

    class _Cursor:
        def fetchone(self):
            return [0]

    class FakeConn:
        def __init__(self, actions):
            self._actions = actions if isinstance(actions, list) else [actions]

        def execute(self, sql, *a, **kw):
            if not self._actions:
                return _Cursor()
            action = self._actions.pop(0)
            if isinstance(action, Exception):
                raise action
            return _Cursor()

        def commit(self):
            pass

        def cursor(self):
            return self

        def fetchall(self):
            return []

        def executemany(self, sql, data):
            pass

        def close(self):
            pass

    calls = {"n": 0}

    def fake_connect(path, timeout=0.0):
        idx = calls["n"]
        calls["n"] += 1
        # once the script is exhausted, behave as a plain successful connection
        actions = script[idx] if idx < len(script) else []
        return FakeConn(actions)

    return fake_connect


def test_check_db_file_second_probe_recovers(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    db.write_bytes(b"garbage")
    monkeypatch.setattr(cm.sqlite3, "connect", _scripted_connect([sqlite3.DatabaseError("1st bad"), None]))
    h = _Holder()
    assert h._check_db_file() is True  # 2nd probe succeeds -> usable, no quarantine
    assert db.read_bytes() == b"garbage"  # untouched


def test_check_db_file_second_probe_operational(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    db.write_bytes(b"garbage")
    monkeypatch.setattr(
        cm.sqlite3,
        "connect",
        _scripted_connect([sqlite3.DatabaseError("1st bad"), sqlite3.OperationalError("2nd locked")]),
    )
    h = _Holder()
    with pytest.warns(RuntimeWarning, match="disabled"):
        assert h._check_db_file() is False


def test_quarantine_moves_sidecars(monkeypatch, tmp_path):
    """Real SQLite deletes stale sidecars of a corrupt db on open, so drive
    quarantine through the scripted connection to reach the sidecar branch."""
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    db.write_bytes(b"garbage")
    (tmp_path / "bib-lookup-cache.db-wal").write_bytes(b"wal")
    (tmp_path / "bib-lookup-cache.db-shm").write_bytes(b"shm")
    monkeypatch.setattr(
        cm.sqlite3, "connect", _scripted_connect([sqlite3.DatabaseError("bad"), sqlite3.DatabaseError("still bad")])
    )
    h = _Holder()
    with pytest.warns(UserWarning, match="corrupt"):
        assert h._init_db() is True
    moved = sorted(p.name for p in tmp_path.glob("*.corrupt-*"))
    assert len(moved) == 3, moved  # db + -wal + -shm all quarantined
    # (real-database recreation is asserted by test_corrupt_db_quarantined_not_deleted)


def test_quarantine_sidecar_rename_oserror_is_best_effort(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    db.write_bytes(b"garbage")
    (tmp_path / "bib-lookup-cache.db-wal").write_bytes(b"wal")
    real_rename = Path.rename

    def selective_rename(self, target):
        if str(self).endswith(("-wal", "-shm")):
            raise OSError("synthetic: sidecar rename refused")
        return real_rename(self, target)

    monkeypatch.setattr(Path, "rename", selective_rename)
    monkeypatch.setattr(
        cm.sqlite3, "connect", _scripted_connect([sqlite3.DatabaseError("bad"), sqlite3.DatabaseError("still bad")])
    )
    h = _Holder()
    with pytest.warns(UserWarning, match="corrupt"):
        assert h._init_db() is True  # db quarantined despite sidecar refusal
    assert len(list(tmp_path.glob("bib-lookup-cache.db.corrupt-*"))) == 1
    assert (tmp_path / "bib-lookup-cache.db-wal").exists()  # left in place


def test_quarantine_rename_oserror_disables(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    db.write_bytes(b"garbage")

    def raise_rename(self, target):
        raise OSError("synthetic: rename refused")

    monkeypatch.setattr(Path, "rename", raise_rename)
    h = _Holder()
    with pytest.warns(RuntimeWarning, match="disabled"):
        assert h._check_db_file() is False
    assert db.read_bytes() == b"garbage"  # still there, never deleted


def test_init_db_databaseerror_branch(monkeypatch, tmp_path):
    _patch_cache_paths(monkeypatch, tmp_path)

    @contextmanager
    def synth_dberror(self, commit=False):
        raise sqlite3.DatabaseError("synthetic malformed schema")
        yield None  # pragma: no cover

    monkeypatch.setattr(cm.CitationMixin, "_open_db", synth_dberror)
    h = _Holder()
    with pytest.warns(RuntimeWarning, match="disabled"):
        assert h._init_db() is False


def _open_db_failing_on(when, skip_commits=0):
    """Build an _open_db replacement that raises OperationalError on the
    selected call shape ("read" for commit=False, "commit" for commit=True),
    delegating everything else to the real implementation.  ``skip_commits``
    lets the first N commit=True calls through (e.g. the _init_db schema
    pass) so a later write-back is what actually fails."""
    orig = cm.CitationMixin._open_db
    commits_seen = {"n": 0}

    @contextmanager
    def patched(self, commit=False):
        if not commit and when == "read":
            raise sqlite3.OperationalError("synthetic failure on read")
        if commit and when == "commit":
            commits_seen["n"] += 1
            if commits_seen["n"] > skip_commits:
                raise sqlite3.OperationalError("synthetic failure on commit")
        with orig(self, commit=commit) as conn:
            yield conn

    return patched


def test_get_citation_read_failure_falls_back_to_network(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm.CitationMixin, "_open_db", _open_db_failing_on("read"))
    h = _Holder(doi="10.1/locked-read")
    h._bl = _mock_bl()
    with pytest.warns(RuntimeWarning, match="disabled"):
        res = h.get_citation()  # read fails -> disable, fall back to network
    assert res == "@article{10.1/locked-read}"


def test_get_citation_write_failure_keeps_result(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm.CitationMixin, "_open_db", _open_db_failing_on("commit", skip_commits=1))
    h = _Holder(doi="10.1/w1")
    h._bl = _mock_bl()
    res = h.get_citation()  # write-back fails -> cache disabled, result intact
    assert res == "@article{10.1/w1}"
    h2 = _Holder(doi="10.1/w1b")  # globally disabled: silent, network-only
    h2._bl = _mock_bl()
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert h2.get_citation() == "@article{10.1/w1b}"


def test_update_cache_write_failure(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm.CitationMixin, "_open_db", _open_db_failing_on("commit", skip_commits=1))
    h = _Holder()
    h._bl = _mock_bl()
    with pytest.warns(RuntimeWarning, match="disabled"):
        h.update_cache(doi="10.1/uc")  # read ok, fetch ok, write fails
    assert db.exists()


def test_update_cache_read_failure(monkeypatch, tmp_path):
    db, _csv = _patch_cache_paths(monkeypatch, tmp_path)
    monkeypatch.setattr(cm.CitationMixin, "_open_db", _open_db_failing_on("read"))
    h = _Holder()
    h._bl = _mock_bl()
    with pytest.warns(RuntimeWarning, match="disabled"):
        h.update_cache(doi="10.1/uc")  # read fails -> disable, no raise
    assert db.exists()


# --- _const twins ---


def test_const_temp_fallback_oserror(monkeypatch, tmp_path):
    if RUNS_AS_ROOT:
        pytest.skip("chmod is ineffective for root")
    home = tmp_path / "home"
    (home / ".cache").mkdir(parents=True)
    (home / ".cache").chmod(0o500)
    monkeypatch.setattr(_const, "CACHE_DIR", home / ".cache" / "bib-lookup")
    monkeypatch.delenv("BIB_LOOKUP_CACHE_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)

    def raise_mkdtemp(*a, **kw):
        raise OSError("synthetic: no temp space")

    monkeypatch.setattr(_const.tempfile, "mkdtemp", raise_mkdtemp)
    resolved, is_temporary = _const._resolve_cache_dir()
    assert resolved is None and is_temporary is False
    (home / ".cache").chmod(0o755)


def test_get_cache_dir_none_warns_once(monkeypatch):
    monkeypatch.setattr(_const, "_resolve_cache_dir", lambda: (None, False))
    _const._CACHE_DIR_RESOLVED = _const._UNSET
    with pytest.warns(RuntimeWarning, match="caching is disabled"):
        assert _const.get_cache_dir() is None
    # memoized: second call silent
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        assert _const.get_cache_dir() is None
    _const._CACHE_DIR_RESOLVED = _const._UNSET


def test_get_cache_dir_temporary_warns(monkeypatch, tmp_path):
    if RUNS_AS_ROOT:
        pytest.skip("chmod is ineffective for root")
    cache_root = tmp_path / "home" / ".cache" / "bib-lookup"
    cache_root.mkdir(parents=True)
    cache_root.chmod(0o500)
    monkeypatch.setattr(_const, "CACHE_DIR", cache_root)
    monkeypatch.delenv("BIB_LOOKUP_CACHE_DIR", raising=False)
    monkeypatch.delenv("XDG_CACHE_HOME", raising=False)
    _const._CACHE_DIR_RESOLVED = _const._UNSET
    with pytest.warns(RuntimeWarning, match="temporary cache directory"):
        d = _const.get_cache_dir()
    assert d is not None and str(d).startswith(tempfile.gettempdir())
    _const._CACHE_DIR_RESOLVED = _const._UNSET
    cache_root.chmod(0o755)
