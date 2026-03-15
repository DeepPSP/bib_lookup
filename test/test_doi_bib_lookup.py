""" """

from collections import OrderedDict

import pytest

import bib_lookup

doi_examples = {
    "DOI: 10.1142/S1005386718000305": "@article{Wen_2018,\n      title = {Counting Multiplicities in a Hypersurface over Number Fields},\n     author = {Wen, Hao and Liu, Chunhui},\n    journal = {Algebra Colloquium},\n     volume = {25},\n       issn = {0219-1733},\n        doi = {10.1142/s1005386718000305},\n     number = {03},\n  publisher = {World Scientific Pub Co Pte Lt},\n       year = {2018},\n      month = {8},\n      pages = {437–458}\n}",
    "10.1109/ICCVW.2019.00246": "@inproceedings{Cao_2019,\n      title = {GCNet: Non-Local Networks Meet Squeeze-Excitation Networks and Beyond},\n     author = {Cao, Yue and Xu, Jiarui and Lin, Stephen and Wei, Fangyun and Hu, Han},\n  booktitle = {2019 IEEE/CVF International Conference on Computer Vision Workshop (ICCVW)},\n        doi = {10.1109/iccvw.2019.00246},\n  publisher = {IEEE},\n       year = {2019},\n      month = {10},\n      pages = {1971–1980}\n}",
    "10.1109/tpami.2019.2913372": "@article{Hu_2020,\n      title = {Squeeze-and-Excitation Networks},\n     author = {Hu, Jie and Shen, Li and Albanie, Samuel and Sun, Gang and Wu, Enhua},\n    journal = {IEEE Transactions on Pattern Analysis and Machine Intelligence},\n     volume = {42},\n       issn = {1939-3539},\n        doi = {10.1109/tpami.2019.2913372},\n     number = {8},\n  publisher = {Institute of Electrical and Electronics Engineers (IEEE)},\n       year = {2020},\n      month = {8},\n      pages = {2011–2023}\n}",
    "doi.org/10.1007/s11263-019-01198-w": "@article{Wu_2019,\n      title = {Group Normalization},\n     author = {Wu, Yuxin and He, Kaiming},\n    journal = {International Journal of Computer Vision},\n     volume = {128},\n       issn = {1573-1405},\n        doi = {10.1007/s11263-019-01198-w},\n     number = {3},\n  publisher = {Springer Science and Business Media LLC},\n       year = {2019},\n      month = {7},\n      pages = {742–755}\n}",
    "https://doi.org/10.23919/cinc53138.2021.9662801": "@inproceedings{Wen_2021,\n      title = {Hybrid Arrhythmia Detection on Varying-Dimensional Electrocardiography: Combining Deep Neural Networks and Clinical Rules},\n     author = {Wen, Hao and Kang, Jingsu},\n  booktitle = {2021 Computing in Cardiology (CinC)},\n        doi = {10.23919/cinc53138.2021.9662801},\n  publisher = {IEEE},\n       year = {2021},\n      month = {9},\n      pages = {1–4}\n}",
}


# bl = bib_lookup.BibLookup(ignore_fields="none")
bl = bib_lookup.BibLookup()
bl.debug()
bl_no_ignore = bib_lookup.BibLookup(ignore_fields="none")


def test_doi_bib_lookup():
    for doi, lookup_result in doi_examples.items():
        bib_string = bl(doi, timeout=1000, verbose=3)
        assert bib_string == lookup_result, f"{doi} mismatch"

        assert bib_lookup.bib_lookuper(doi, timeout=1000, ignore_fields="doi") is None

        assert bl(doi, timeout=1000, format="text") is not None

    assert bl(list(doi_examples), timeout=1000, print_result=True, verbose=10) is None

    assert bl("doi: xxx/xxx") == bl.default_err

    assert bl.cache_limit is not None

    bl.print()

    assert isinstance(bl.get_cache(), OrderedDict)
    assert isinstance(bl.get_cache(string_format=True), str)

    with pytest.raises(ValueError):
        bib_lookup.BibLookup(cache_limit="xxx")

    # test no ignore fields
    bl_no_ignore("DOI: 10.1142/S1005386718000305", timeout=1000)

    # test ChinaDOI
    china_doi = "10.13748/j.cnki.issn1007-7693.20251689"
    bib_string = bl(china_doi, timeout=1000, verbose=3)
    assert bib_string.startswith(bib_lookup.BibLookup.__REDIRECT_FLAG__), bib_string  # type: ignore

    # Test text format with style (covers lines 630-634)
    text_result = bl("10.1142/S1005386718000305", timeout=1000, format="text", style="ieee")
    assert text_result is not None

    # Test text format with unsupported style (covers lines 635-638)
    text_result_other = bl("10.1142/S1005386718000305", timeout=1000, format="text", style="unsupported_style")
    assert text_result_other is not None

    # Test verbose >= 1 with error (covers lines 639-642)
    bl_verbose = bib_lookup.BibLookup(verbose=1)
    err_result = bl_verbose("doi: invalid_doi_for_testing", timeout=1000)
    assert err_result in bl_verbose.lookup_errors

    # Test ignore_errors=True (covers line 645)
    bl_ignore = bib_lookup.BibLookup(ignore_errors=True)
    result_ignore = bl_ignore("doi: invalid_doi_for_testing", timeout=1000)
    assert result_ignore == ""

    # Test capitalize_title=True (covers lines 1092-1093)
    bl_cap = bib_lookup.BibLookup(capitalize_title=True)
    bib_cap = bl_cap("10.1142/S1005386718000305", timeout=1000)
    assert bib_cap is not None

    # Test with label parameter (covers lines 1058-1060)
    bib_labeled = bl("10.1142/S1005386718000305", timeout=1000, label="custom_label")
    assert "custom_label" in bib_labeled

    # Test dict input for _to_bib_item (covers lines 1043-1046)
    bl._to_bib_item({"title": "Test", "author": "Author", "entry_type": "article", "label": "test"}, "test_id")

    # Test field with braces (covers lines 1077-1078)
    bl._to_bib_item("@article{test,\n  title = {Test Title},\n  author = {Author}\n}", "test_id")

    # Test _handle_doi with format="text" (covers lines 708-709)
    bl_text = bib_lookup.BibLookup(format="text")
    bl_text._handle_doi({"url": "https://doi.org/10.1142/S1005386718000305", "timeout": 1000})

    # Test _handle_doi with verbose > 3 (covers lines 805-814)
    bl_v3 = bib_lookup.BibLookup(verbose=4)
    result_v3 = bl_v3("10.1142/S1005386718000305", timeout=1000)
    assert result_v3 is not None

    # Test _handle_doi fallback (covers lines 847-852)
    bl_fallback = bib_lookup.BibLookup(verbose=4)
    result_fallback = bl_fallback("10.1142/S1005386718000305", timeout=1000, format="text")
    assert result_fallback is not None

    # Test _handle_doi non-200 response (covers line 862)
    bl_non200 = bib_lookup.BibLookup()
    # This tests the fallback path when initial request fails
    result_non200 = bl_non200("10.1142/S1005386718000305", timeout=1000)
    assert result_non200 is not None
