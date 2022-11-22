from pathlib import Path

import pandas as pd

import bib_lookup


_CWD = Path(__file__).resolve().parent

df_cache_before_update = pd.read_csv(_CWD / "cache-before-update.csv")
df_cache_after_update = pd.read_csv(_CWD / "cache-after-update.csv")


class SomeClass(bib_lookup.CitationMixin):
    def __init__(self):
        pass

    @property
    def doi(self):
        return ["10.1142/s1005386718000305"]


def test_citation_mixin():
    if bib_lookup.CitationMixin.citation_cache.exists():
        df_system_cache = pd.read_csv(bib_lookup.CitationMixin.citation_cache)
    else:
        df_system_cache = None
    df_cache_before_update.to_csv(bib_lookup.CitationMixin.citation_cache, index=False)

    obj = SomeClass()
    obj.update_cache()
    assert pd.read_csv(bib_lookup.CitationMixin.citation_cache).equals(
        df_cache_after_update
    )

    if df_system_cache is not None:
        df_system_cache.to_csv(bib_lookup.CitationMixin.citation_cache, index=False)
