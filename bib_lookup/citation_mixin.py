"""
"""

import warnings
from pathlib import Path
from typing import Optional, Union, Sequence

import pandas as pd

from .bib_lookup import BibLookup


__all__ = [
    "CitationMixin",
]


_CACHE_DIR = Path("~").expanduser() / ".cache" / "bib-lookup"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class CitationMixin(object):
    """
    Mixin class for getting citations from DOIs.
    """

    _bl = BibLookup(timeout=1.0, ignore_errors=False)

    citation_cache = _CACHE_DIR / "bib-lookup-cache.csv"

    def get_citation(
        self,
        lookup: bool = True,
        format: Optional[str] = None,
        style: Optional[str] = None,
        timeout: Optional[float] = None,
        print_result: bool = False,
    ) -> Union[str, type(None)]:
        """
        Parameters
        ----------
        lookup: bool, default True,
            whether to lookup the citations from the DOIs,
            if False, will return (or print) the DOIs directly
        format: str, optional,
            format of the final output,
            if specified, the default format ("bib") will be overrided
        style: str, optional,
            style of the final output,
            if specified, the default style ("apa") will be overrided,
            only valid when `format` is "text"
        timeout: float, optional,
            timeout for the lookup,
            only valid when `lookup` is True,
            if not specified, the default timeout (1.0) will be used
        print_result: bool, default False,
            whether to print the final output instead of returning it

        Returns
        -------
        str, optional,
            citation(s) of the database

        """
        self._bl.clear_cache()
        if self.citation_cache.exists():
            df_cc = pd.read_csv(self.citation_cache)
        else:
            df_cc = pd.DataFrame(columns=["doi", "citation"])
            df_cc.to_csv(self.citation_cache, index=False)

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
            if format is not None and format != self._bl.format:
                citation = ""  # no cache for format other than bibtex
            else:
                citation = "\n".join(df_cc[df_cc["doi"].isin(doi)]["citation"].tolist())
                doi = [item for item in doi if item not in df_cc["doi"].tolist()]
                if print_result:
                    print(citation)
            if len(doi) > 0:
                new_citations = []
                for item in doi:
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
                    new_citations = [
                        item
                        for item in new_citations
                        if item["citation"] is not None
                        and item["citation"].startswith("@")
                    ]
                    df_new = pd.DataFrame(new_citations)
                    if len(df_new) > 0:
                        df_new.to_csv(
                            self.citation_cache, mode="a", header=False, index=False
                        )
                else:
                    df_new = pd.DataFrame(new_citations)
                if len(df_new) > 0:
                    citation += "\n" + "\n".join(df_new["citation"].tolist())
        else:
            citation = ""

        citation = citation.strip("\n ")
        if citation == "" and self.doi is not None:
            citation = "\n".join(doi)
            warnings.warn("Lookup failed, defaults to the DOI(s).")
            if print_result:
                print(citation)
        if not print_result:
            return citation

    def update_cache(self, doi: Optional[Union[str, Sequence[str]]] = None) -> None:
        """
        Update the cache.

        Parameters
        ----------
        doi: str or sequence of str, optional,
            DOIs to update the cache,
            if not specified, will update the whole cache

        """
        if self.citation_cache.exists():
            df_cc = pd.read_csv(self.citation_cache)
        else:
            df_cc = pd.DataFrame(columns=["doi", "citation"])
        if doi is None:
            doi = df_cc.doi.tolist()
        if isinstance(doi, str):
            doi = [doi]

        new_citations = []
        for item in doi:
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
        df_cc = pd.concat([df_cc, pd.DataFrame(new_citations)])
        df_cc = df_cc.drop_duplicates(subset="doi", keep="last", ignore_index=True)
        df_cc.to_csv(self.citation_cache, index=False)
