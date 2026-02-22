""" """

import sqlite3
import warnings
from typing import Optional, Sequence, Union

import pandas as pd

from ._const import CACHE_DIR
from .bib_lookup import BibLookup

__all__ = [
    "CitationMixin",
]


class CitationMixin(object):
    """
    Mixin class for getting citations from DOIs.
    """

    _bl = BibLookup(timeout=1.0, ignore_errors=False)

    citation_cache_csv = CACHE_DIR / "bib-lookup-cache.csv"
    citation_cache_db = CACHE_DIR / "bib-lookup-cache.db"
    citation_cache = citation_cache_db

    def _init_db(self):
        """Initialize sqlite db and migrate csv if exists."""
        conn = sqlite3.connect(self.citation_cache_db)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS citations (
                doi TEXT PRIMARY KEY,
                citation TEXT
            )
        """)

        # Backward compatibility: Migrate CSV to SQLite
        if self.citation_cache_csv.exists():
            try:
                df = pd.read_csv(self.citation_cache_csv)
                # Batch insert data, use OR IGNORE to avoid duplicates
                data = list(df[["doi", "citation"]].itertuples(index=False, name=None))
                cursor.executemany(
                    "INSERT OR IGNORE INTO citations (doi, citation) VALUES (?, ?)",
                    data,
                )
                conn.commit()
                # Delete CSV after successful migration
                self.citation_cache_csv.unlink()
                print(f"Migrated citation cache from CSV to SQLite: {self.citation_cache_db}")
            except Exception as e:
                print(f"Failed to migrate CSV cache: {e}")

        conn.commit()
        conn.close()

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
        self._init_db()

        if self.doi is not None:
            if isinstance(self.doi, str):
                doi = [self.doi]
            else:
                doi = self.doi
            if not lookup:
                citation = "\n".join(doi)
                if print_result:
                    print(citation)
                    return
                else:
                    return citation

            # Fetch from cache
            conn = sqlite3.connect(self.citation_cache_db)
            cursor = conn.cursor()

            # Use placeholders for the IN clause
            placeholders = ",".join("?" * len(doi))

            if format is not None and format != self._bl.format:
                citation = ""  # no cache for format other than bibtex
                existing_dois = set()
                cached_citations = []
            else:
                query = f"SELECT citation FROM citations WHERE doi IN ({placeholders})"
                cursor.execute(query, doi)
                cached_citations = [row[0] for row in cursor.fetchall()]
                citation = "\n".join(cached_citations)
                if print_result and citation:
                    print(citation)

                # Find which DOIs were found
                query_exist = f"SELECT doi FROM citations WHERE doi IN ({placeholders})"
                cursor.execute(query_exist, doi)
                existing_dois = {row[0] for row in cursor.fetchall()}

            conn.close()

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

                    if valid_new_citations:
                        conn = sqlite3.connect(self.citation_cache_db)
                        cursor = conn.cursor()
                        data_to_insert = [(item["doi"], item["citation"]) for item in valid_new_citations]
                        cursor.executemany("INSERT OR REPLACE INTO citations (doi, citation) VALUES (?, ?)", data_to_insert)
                        conn.commit()
                        conn.close()

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
        self._init_db()
        conn = sqlite3.connect(self.citation_cache_db)
        cursor = conn.cursor()

        if doi is None:
            cursor.execute("SELECT doi FROM citations")
            doi_list = [row[0] for row in cursor.fetchall()]
        else:
            if isinstance(doi, str):
                doi_list = [doi]
            else:
                doi_list = list(doi)

        conn.close()  # Close connection while fetching to avoid locking issues if fetching takes long

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
            conn = sqlite3.connect(self.citation_cache_db)
            cursor = conn.cursor()
            data_to_insert = [(item["doi"], item["citation"]) for item in new_citations]
            cursor.executemany("INSERT OR REPLACE INTO citations (doi, citation) VALUES (?, ?)", data_to_insert)
            conn.commit()
            conn.close()
