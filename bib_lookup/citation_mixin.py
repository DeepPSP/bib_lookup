""" """

import os
import sqlite3
import warnings
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, List, Optional, Sequence, Set, Tuple, Union

try:
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None

from ._const import DEFAULT_CITATION_CACHE_CSV, DEFAULT_CITATION_CACHE_DB, get_cache_dir
from .bib_lookup import BibLookup

__all__ = [
    "CitationMixin",
]

# Busy timeout (seconds) applied to every sqlite3 connection of the cache.
# Monkeypatched by tests that exercise locked-database scenarios quickly.
SQLITE_TIMEOUT_S = 5.0

# Process-wide state: once the cache is disabled (unusable directory, locked
# db, read-only filesystem, ...), every further CitationMixin instance in this
# process skips it immediately, so that e.g. importing torch_ecg (which
# initializes the cache once per bundled database) stays fast and silent.
_CACHE_DISABLED = False
_DISABLE_WARNED = False


def _reset_cache_disable_state() -> None:
    """Reset the process-wide cache-disabled flag (mainly for tests)."""
    global _CACHE_DISABLED, _DISABLE_WARNED
    _CACHE_DISABLED = False
    _DISABLE_WARNED = False


class CitationMixin(object):
    """
    Mixin class for getting citations from DOIs.
    """

    _bl = BibLookup(timeout=1.0, ignore_errors=False)

    citation_cache_csv = DEFAULT_CITATION_CACHE_CSV
    citation_cache_db = DEFAULT_CITATION_CACHE_DB
    citation_cache = citation_cache_db

    # ------------------------------------------------------------------
    # cache state management
    # ------------------------------------------------------------------

    def _disable_cache(self, reason: str) -> None:
        """Disable citation caching for this process (warn once)."""
        global _CACHE_DISABLED, _DISABLE_WARNED
        _CACHE_DISABLED = True
        self._cache_enabled = False
        if not _DISABLE_WARNED:
            _DISABLE_WARNED = True
            warnings.warn(f"bib_lookup citation cache disabled: {reason}", RuntimeWarning)

    def _resolve_cache(self) -> bool:
        """Resolve the cache paths for this instance.

        Returns True when caching is usable.  An externally overridden
        ``citation_cache_db`` class attribute (tests, embedding applications)
        is honored as-is; otherwise the root directory from
        :func:`bib_lookup._const.get_cache_dir` is used.  Never raises.
        """
        global _CACHE_DISABLED
        self._cache_resolved = True
        if _CACHE_DISABLED:
            self._cache_enabled = False
            return False
        cls = type(self)
        if cls.citation_cache_db != DEFAULT_CITATION_CACHE_DB:
            # externally overridden: honor as-is (the overrider owns the path)
            db, csv = cls.citation_cache_db, cls.citation_cache_csv
        else:
            root = get_cache_dir()
            if root is None:
                self.citation_cache_db = None
                self.citation_cache_csv = None
                self.citation_cache = None
                self._cache_enabled = False
                return False
            db, csv = root / "bib-lookup-cache.db", root / "bib-lookup-cache.csv"
        if db is None:
            self._cache_enabled = False
            return False
        try:
            Path(db).parent.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            self._disable_cache(f"cannot create cache directory ({e})")
            return False
        self.citation_cache_db = db
        self.citation_cache_csv = csv
        self.citation_cache = db
        self._cache_enabled = True
        return True

    # ------------------------------------------------------------------
    # sqlite plumbing
    # ------------------------------------------------------------------

    @contextmanager
    def _init_lock(self) -> Iterator[None]:
        """Serialize cache-file initialization across processes.

        The probe/quarantine/schema sequence below is multi-step and not
        atomic; without this lock, a concurrent first-time initializer could
        probe a half-written database, "quarantine" the live file under its
        creator and split the cache.  Best effort: on platforms without
        fcntl (or filesystems that refuse the lock) initialization simply
        proceeds unlocked.
        """
        if fcntl is None:
            yield
            return
        lock_path = Path(self.citation_cache_db).with_name(Path(self.citation_cache_db).name + ".init-lock")
        try:
            lock_path.parent.mkdir(parents=True, exist_ok=True)
            fh = open(lock_path, "w")
        except OSError:
            # e.g. read-only cache directory: proceed without the lock; the
            # probe below will disable the cache on its own
            yield
            return
        try:
            try:
                fcntl.flock(fh, fcntl.LOCK_EX)
            except OSError:
                pass  # best effort: e.g. exotic network filesystems
            yield
        finally:
            try:
                fcntl.flock(fh, fcntl.LOCK_UN)
            except OSError:
                pass
            fh.close()

    @contextmanager
    def _open_db(self, commit: bool = False) -> Iterator[sqlite3.Connection]:
        """Open a cache connection; always close it (even on exceptions)."""
        conn = sqlite3.connect(self.citation_cache_db, timeout=SQLITE_TIMEOUT_S)
        try:
            yield conn
            if commit:
                conn.commit()
        finally:
            conn.close()

    def _check_db_file(self) -> bool:
        """Validate an existing cache database file; quarantine corrupt ones.

        Returns True when the file is absent or usable.  Operational errors
        (locked database, permission denied, read-only filesystem, ...) are
        NOT corruption: they disable the cache and never touch the file.  A
        genuinely malformed file is verified twice (to avoid racing with a
        concurrent cache creator) and then renamed aside to
        ``<name>.corrupt-<timestamp>-<pid>`` instead of being deleted, so the
        data remains recoverable by hand.
        """
        db = Path(self.citation_cache_db)
        if not db.exists():
            return True

        def _probe() -> None:
            conn = sqlite3.connect(db, timeout=SQLITE_TIMEOUT_S)
            try:
                conn.execute("SELECT count(*) FROM sqlite_master").fetchone()
            finally:
                conn.close()

        try:
            _probe()
            return True
        except sqlite3.OperationalError as e:
            # unable to open / locked / permission denied / read-only fs --
            # never treat these as corruption and never delete the file
            self._disable_cache(f"citation cache unusable ({e})")
            return False
        except sqlite3.DatabaseError as e:
            # possible corruption; re-verify before quarantining, since the
            # file may have been (re)created concurrently after the first probe
            try:
                _probe()
                return True  # usable now -- someone else rebuilt it in between
            except sqlite3.OperationalError as e2:
                self._disable_cache(f"citation cache unusable ({e2})")
                return False
            except sqlite3.DatabaseError:
                pass  # still malformed -> quarantine below
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            quarantine = db.with_name(f"{db.name}.corrupt-{stamp}-{os.getpid()}")
            warnings.warn(
                f"Citation cache database is corrupt and will be recreated: {db} "
                f"(original moved to {quarantine.name})",
                UserWarning,
            )
            try:
                db.rename(quarantine)
                for suffix in ("-wal", "-shm"):
                    side = db.with_name(db.name + suffix)
                    if side.exists():
                        try:
                            side.rename(side.with_name(side.name + f".corrupt-{stamp}-{os.getpid()}"))
                        except OSError:
                            pass  # best effort: sidecars of a corrupt db are garbage
            except OSError as e3:
                self._disable_cache(f"cannot quarantine corrupt cache file ({e3})")
                return False
            return True

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def _init_db(self) -> bool:
        """Initialize sqlite db and migrate the legacy csv cache if present.

        Returns True when the cache is usable.  Never raises: any failure
        disables caching (with a single warning) instead of propagating into
        the caller (e.g. ``import torch_ecg``).
        """
        if not self._resolve_cache():
            return False
        try:
            # probe / quarantine / schema creation must not interleave with a
            # concurrent first-time initializer (see _init_lock)
            with self._init_lock():
                if not self._check_db_file():
                    return False

                with self._open_db(commit=True) as conn:
                    cursor = conn.cursor()
                    # WAL mode allows concurrent readers alongside a writer, reducing
                    # contention and corruption risk when multiple processes share the db.
                    cursor.execute("PRAGMA journal_mode=WAL")
                    # CREATE TABLE IF NOT EXISTS is idempotent: safe to call every time,
                    # including when multiple xdist workers race through this method.
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS citations (
                            doi TEXT PRIMARY KEY,
                            citation TEXT
                        )
                    """)
                    conn.commit()

                # Backward compatibility: Migrate CSV to SQLite
                if self.citation_cache_csv is not None and Path(self.citation_cache_csv).exists():
                    try:
                        import pandas as pd

                        df = pd.read_csv(self.citation_cache_csv)
                        # Batch insert data, use OR IGNORE to avoid duplicates
                        data = list(df[["doi", "citation"]].itertuples(index=False, name=None))
                        with self._open_db(commit=True) as conn:
                            conn.executemany(
                                "INSERT OR IGNORE INTO citations (doi, citation) VALUES (?, ?)",
                                data,
                            )
                        # Delete CSV after successful migration
                        self.citation_cache_csv.unlink()
                        warnings.warn(f"Migrated citation cache from CSV to SQLite: {self.citation_cache_db}", UserWarning)
                    except Exception as e:
                        warnings.warn(f"Failed to migrate CSV cache: {e}", UserWarning)
        except sqlite3.OperationalError as e:
            # locked db, permission denied, read-only fs, ... -- never delete,
            # just run without the cache
            self._disable_cache(f"cannot initialize citation cache ({e})")
            return False
        except sqlite3.DatabaseError as e:
            self._disable_cache(f"citation cache initialization failed ({e})")
            return False
        return True

    def get_citation(
        self,
        lookup: bool = True,
        format: Optional[str] = None,
        style: Optional[str] = None,
        timeout: Optional[float] = None,
        print_result: bool = False,
    ) -> Union[str, None]:
        """Get the bib citation(s) from the DOI(s).

        Parameters
        ----------
        lookup : bool, default True
            Whether to look up the citation from the cache.
        format : str, optional
            The format of the citation. If not specified, the citation
            will be returned in the default format (bibtex).
        style : str, optional
            The style of the citation. If not specified, the citation
            will be returned in the default style (apa).
            Valid only when `format` is ``"text"``.
        timeout : float, optional
            The timeout for the request.
        print_result : bool, default False
            Whether to print the citation.

        Returns
        -------
        str or None
            bib citation(s) from the DOI(s),
            or None if `print_result` is True.

        """
        self._bl.clear_cache()
        cache_on = self._init_db()

        if self.doi is not None:
            if isinstance(self.doi, str):
                doi = [self.doi]
            else:
                doi = self.doi

            # If doi is empty, return empty result
            if not doi:
                if print_result:
                    return
                else:
                    return ""

            if not lookup:
                citation = "\n".join(doi)
                if print_result:
                    print(citation)
                    return
                else:
                    return citation

            # Fetch from cache (bibtex format only)
            cached_citations: List[str] = []
            existing_dois: Set[str] = set()
            cache_readable = cache_on and (format is None or format == self._bl.format)

            if cache_readable:
                # SQLite has a limit on the number of variables in a query (default 999).
                # We chunk the DOIs to avoid hitting this limit.
                chunk_size = 900
                try:
                    with self._open_db() as conn:
                        cursor = conn.cursor()
                        for i in range(0, len(doi), chunk_size):
                            chunk = doi[i : i + chunk_size]
                            if not chunk:
                                continue

                            placeholders = ",".join("?" * len(chunk))

                            query = f"SELECT citation FROM citations WHERE doi IN ({placeholders})"
                            cursor.execute(query, chunk)
                            cached_citations.extend([row[0] for row in cursor.fetchall()])

                            query_exist = f"SELECT doi FROM citations WHERE doi IN ({placeholders})"
                            cursor.execute(query_exist, chunk)
                            existing_dois.update({row[0] for row in cursor.fetchall()})
                except sqlite3.OperationalError as e:
                    # locked db / permissions / ...: fall back to network only
                    self._disable_cache(f"citation cache read failed ({e})")
                    cached_citations, existing_dois = [], set()

            citation = "\n".join(cached_citations)
            if print_result and citation:
                print(citation)

            # Filter out DOIs that were found in cache
            doi_to_fetch = [item for item in doi if item not in existing_dois]

            if len(doi_to_fetch) > 0:
                new_citations = []
                for item in doi_to_fetch:
                    try:
                        bl_res = self._bl(
                            item,
                            format=format,
                            style=style,
                            print_result=False,
                            timeout=timeout,
                        )
                        if bl_res not in self._bl.lookup_errors:
                            new_citations.append(
                                {
                                    "doi": item,
                                    "citation": str(bl_res),
                                }
                            )
                            if print_result:
                                print(bl_res)
                        elif print_result:
                            print(f"{bl_res} for {item}")
                    except Exception:
                        if print_result:
                            print(f"Failed to lookup citation for {item}")

                if format is None or format == self._bl.format:
                    # only cache bibtex format
                    # Filter for valid bibtex citations (starting with @)
                    valid_new_citations = [
                        item
                        for item in new_citations
                        if item["citation"] is not None and item["citation"].strip().startswith("@")
                    ]

                    if cache_on and valid_new_citations:
                        try:
                            with self._open_db(commit=True) as conn:
                                data_to_insert = [(item["doi"], item["citation"]) for item in valid_new_citations]
                                conn.executemany(
                                    "INSERT OR REPLACE INTO citations (doi, citation) VALUES (?, ?)", data_to_insert
                                )
                        except sqlite3.OperationalError as e:
                            self._disable_cache(f"citation cache write failed ({e})")

                # Update the returned citation string with newly fetched citations
                additional_citations = [item["citation"] for item in new_citations]
                if additional_citations:
                    if citation:
                        citation += "\n" + "\n".join(additional_citations)
                    else:
                        citation = "\n".join(additional_citations)
        else:
            citation = ""
            doi = []

        citation = citation.strip("\n ")
        if citation == "" and self.doi is not None:
            citation = "\n".join(doi)
            warnings.warn("Lookup failed, defaults to the DOI(s).", RuntimeWarning)
            if print_result:
                print(citation)
        if not print_result:
            return citation

    def update_cache(self, doi: Optional[Union[str, Sequence[str]]] = None) -> None:
        """Update the cache.

        Parameters
        ----------
        doi : str or Sequence[str], optional
            DOIs to update the cache
            If not specified, the whole cache will be updated.

        Returns
        -------
        None

        """
        if not self._init_db():
            return
        try:
            with self._open_db() as conn:
                cursor = conn.cursor()
                if doi is None:
                    cursor.execute("SELECT doi FROM citations")
                    doi_list: List[str] = [row[0] for row in cursor.fetchall()]
                else:
                    if isinstance(doi, str):
                        doi_list = [doi]
                    else:
                        doi_list = list(doi)
        except sqlite3.OperationalError as e:
            self._disable_cache(f"citation cache read failed ({e})")
            return

        new_citations = []
        for item in doi_list:
            try:
                bl_res = self._bl(item, timeout=10.0)
                if bl_res not in self._bl.lookup_errors:
                    new_citations.append(
                        {
                            "doi": item,
                            "citation": str(bl_res),
                        }
                    )
            except Exception:
                print(f"Failed to lookup citation for {item}")

        if new_citations:
            try:
                with self._open_db(commit=True) as conn:
                    data_to_insert = [(item["doi"], item["citation"]) for item in new_citations]
                    conn.executemany("INSERT OR REPLACE INTO citations (doi, citation) VALUES (?, ?)", data_to_insert)
            except sqlite3.OperationalError as e:
                self._disable_cache(f"citation cache write failed ({e})")
