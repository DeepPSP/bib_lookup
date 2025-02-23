from pathlib import Path

import pandas as pd

import bib_lookup

_CWD = Path(__file__).resolve().parent

df_cache_before_update = pd.read_csv(_CWD.parent / "sample-files" / "cache-before-update.csv")
df_cache_after_update = pd.read_csv(_CWD.parent / "sample-files" / "cache-after-update.csv")


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


def test_citation_mixin():
    if bib_lookup.CitationMixin.citation_cache.exists():
        df_system_cache = pd.read_csv(bib_lookup.CitationMixin.citation_cache)
    else:
        df_system_cache = None
    df_cache_before_update.to_csv(bib_lookup.CitationMixin.citation_cache, index=False)

    obj = SomeClass()
    obj.update_cache()
    df_citation_cache = pd.read_csv(bib_lookup.CitationMixin.citation_cache)
    match = df_citation_cache.equals(df_cache_after_update)
    if not match:
        mismatch_list = df_citation_cache.compare(df_cache_after_update).values.tolist()
        mismatch_list = ("\n" + "+" * 80 + "\n").join(["\n".join(row) for row in mismatch_list])
    else:
        mismatch_list = None
    assert match, f"mismatch list = {mismatch_list}"

    if df_system_cache is not None:
        df_system_cache.to_csv(bib_lookup.CitationMixin.citation_cache, index=False)

    assert obj.get_citation() is not None
    assert obj.get_citation(format="text") is not None
    assert obj.get_citation(lookup=False) is not None
    assert obj.get_citation(print_result=True) is None
    assert obj.get_citation(lookup=False, print_result=True) is None

    obj = AnotherClass()
    assert obj.get_citation() is not None
    assert obj.get_citation(print_result=True) is None
    obj.update_cache(doi="10.1142/s1005386718000305")

    if obj.citation_cache.exists():
        obj.citation_cache.unlink()

    obj = YetAnotherClass()
    assert obj.get_citation() == ""
    assert str(obj) == repr(obj) == "YetAnotherClass"
