import pytest
from pybtex.database import Entry, Person
from pybtex.style.template import Node

from bib_lookup.styles.apa import APANames, APAStyle
from bib_lookup.styles.chicago import ChicagoNames, ChicagoStyle, chicago_date, chicago_date_plain, chicago_pages
from bib_lookup.styles.gbt7714 import GBT7714Style, GBTNames, gbt_year_vol_pages
from bib_lookup.styles.ieee import IEEENames, IEEEStyle, ieee_month, ieee_pages

EXAMPLES = [
    {
        "entry": """
@article{qi2021kemre,
      title = {{KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions}},
     author = {Tao Qi and Shan Qiu and Xiaoqian Shen and Haopu Chen and Shuai Yang and Hao Wen and Ya Zhang and Yuanqing Wu and Yongfeng Huang},
    journal = {{Journal of Biomedical Informatics}},
        doi = {10.1016/j.jbi.2021.103834},
       year = {2021},
      month = {8},
  publisher = {{Elsevier BV}},
     volume = {120},
      pages = {103834}
}""",
        "apa": """Qi, T., Qiu, S., Shen, X., Chen, H., Yang, S., Wen, H., Zhang, Y., Wu, Y., & Huang, Y. (2021). KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions. Journal of Biomedical Informatics, 120, 103834. https://doi.org/10.1016/j.jbi.2021.103834""",
        "ieee": """[1] Tao Qi et al. “KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions”. In: Journal of Biomedical Informatics 120 (Aug. 2021), p. 103834. doi: 10.1016/j.jbi.2021.103834.""",
        "gbt7714": """[1] QI T, QIU S, SHEN X, et al. KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions[J/OL]. Journal of Biomedical Informatics, 2021, 120: 103834. DOI: 10.1016/j.jbi.2021.103834.""",
        "chicago": """Qi, Tao, Shan Qiu, Xiaoqian Shen, Haopu Chen, Shuai Yang, Hao Wen, Ya Zhang, Yuanqing Wu, and Yongfeng Huang. “KeMRE: Knowledge-Enhanced Medical Relation Extraction for Chinese Medicine Instructions.” Journal of Biomedical Informatics 120 (August 2021): 103834. https://doi.org/10.1016/j.jbi.2021.103834.""",
    },
    # w/ doi, w/o url example
    {
        "entry": """
@article{torch_ecg_paper,
      title = {{A Novel Deep Learning Package for Electrocardiography Research}},
     author = {Wen, Hao and Kang, Jingsu},
    journal = {{Physiological Measurement}},
        doi = {10.1088/1361-6579/ac9451},
       year = {2022},
      month = {11},
  publisher = {{IOP Publishing}},
     volume = {43},
     number = {11},
       issn = {1361-6579},
      pages = {115006}
}""",
        "apa": """Wen, H., & Kang, J. (2022). A Novel Deep Learning Package for Electrocardiography Research. Physiological Measurement, 43(11), 115006. https://doi.org/10.1088/1361-6579/ac9451""",
        "ieee": """[1] H. Wen and J. Kang, “A Novel Deep Learning Package for Electrocardiography Research,” Physiological Measurement, vol. 43, no. 11, p. 115 006, Nov. 2022, ISSN: 1361-6579. DOI: 10.1088/1361-6579/ac9451.""",
        "gbt7714": """[1] WEN H, KANG J. A Novel Deep Learning Package for Electrocardiography Research[J/OL]. Physiological Measurement, 2022, 43(11): 115006. DOI: 10.1088/1361-6579/ac9451.""",
        "chicago": """Wen, Hao, and Jingsu Kang. “A Novel Deep Learning Package for Electrocardiography Research.” Physiological Measurement 43, no. 11 (November 2022): 115006. ISSN: 1361-6579. https://doi.org/10.1088/1361-6579/ac9451.""",
    },
    # w/o doi, w/o url example
    {
        "entry": """
@article{torch_ecg_paper,
      title = {{A Novel Deep Learning Package for Electrocardiography Research}},
     author = {Wen, Hao and Kang, Jingsu},
    journal = {{Physiological Measurement}},
       year = {2022},
      month = {11},
  publisher = {{IOP Publishing}},
     volume = {43},
     number = {11},
       issn = {1361-6579},
      pages = {115006}
}""",
        "apa": """Wen, H., & Kang, J. (2022). A Novel Deep Learning Package for Electrocardiography Research. Physiological Measurement, 43(11), 115006.""",
        "ieee": """[1] H. Wen and J. Kang, “A Novel Deep Learning Package for Electrocardiography Research,” Physiological Measurement, vol. 43, no. 11, p. 115 006, Nov. 2022, ISSN: 1361-6579.""",
        "gbt7714": """[1] WEN H, KANG J. A Novel Deep Learning Package for Electrocardiography Research[J]. Physiological Measurement, 2022, 43(11): 115006.""",
        "chicago": """Wen, Hao, and Jingsu Kang. “A Novel Deep Learning Package for Electrocardiography Research.” Physiological Measurement 43, no. 11 (November 2022): 115006. ISSN: 1361-6579.""",
    },
    # w/o doi, w/ url example
    {
        "entry": """
@article{torch_ecg_paper,
      title = {{A Novel Deep Learning Package for Electrocardiography Research}},
     author = {Wen, Hao and Kang, Jingsu},
    journal = {{Physiological Measurement}},
       year = {2022},
      month = {11},
  publisher = {{IOP Publishing}},
     volume = {43},
     number = {11},
       issn = {1361-6579},
      pages = {115006},
        url = {https://doi.org/10.1088/1361-6579/ac9451}
}""",
        "apa": """Wen, H., & Kang, J. (2022). A Novel Deep Learning Package for Electrocardiography Research. Physiological Measurement, 43(11), 115006. https://doi.org/10.1088/1361-6579/ac9451""",
        "ieee": """[1] H. Wen and J. Kang, “A Novel Deep Learning Package for Electrocardiography Research,” Physiological Measurement, vol. 43, no. 11, p. 115 006, Nov. 2022, ISSN: 1361-6579. [Online]. Available: https://doi.org/10.1088/1361-6579/ac9451.""",
        "gbt7714": """[1] WEN H, KANG J. A Novel Deep Learning Package for Electrocardiography Research[J/OL]. Physiological Measurement, 2022, 43(11): 115006. https://doi.org/10.1088/1361-6579/ac9451.""",
        "chicago": """Wen, Hao, and Jingsu Kang. “A Novel Deep Learning Package for Electrocardiography Research.” Physiological Measurement 43, no. 11 (November 2022): 115006. ISSN: 1361-6579. https://doi.org/10.1088/1361-6579/ac9451.""",
    },
    # w/ doi, w/ url example
    {
        "entry": """
@article{torch_ecg_paper,
      title = {{A Novel Deep Learning Package for Electrocardiography Research}},
     author = {Wen, Hao and Kang, Jingsu},
    journal = {{Physiological Measurement}},
        doi = {10.1088/1361-6579/ac9451},
       year = {2022},
      month = {11},
  publisher = {{IOP Publishing}},
     volume = {43},
     number = {11},
       issn = {1361-6579},
      pages = {115006},
        url = {https://doi.org/10.1088/1361-6579/ac9451}
}""",
        "apa": """Wen, H., & Kang, J. (2022). A Novel Deep Learning Package for Electrocardiography Research. Physiological Measurement, 43(11), 115006. https://doi.org/10.1088/1361-6579/ac9451""",
        "ieee": """[1] H. Wen and J. Kang, “A Novel Deep Learning Package for Electrocardiography Research,” Physiological Measurement, vol. 43, no. 11, p. 115 006, Nov. 2022, ISSN: 1361-6579. DOI: 10.1088/1361-6579/ac9451. URL: https://doi.org/10.1088/1361-6579/ac9451.""",
        "gbt7714": """[1] WEN H, KANG J. A Novel Deep Learning Package for Electrocardiography Research[J/OL]. Physiological Measurement, 2022, 43(11): 115006. https://doi.org/10.1088/1361-6579/ac9451. DOI: 10.1088/1361-6579/ac9451.""",
        "chicago": """Wen, Hao, and Jingsu Kang. “A Novel Deep Learning Package for Electrocardiography Research.” Physiological Measurement 43, no. 11 (November 2022): 115006. ISSN: 1361-6579. https://doi.org/10.1088/1361-6579/ac9451. https://doi.org/10.1088/1361-6579/ac9451.""",
    },
    # no volume / no number (page-range with en-dash)
    {
        "entry": """
@article{Groot_Bruinderink_2018,
      title = {{Differential Fault Attacks on Deterministic Lattice Signatures}},
     author = {Groot Bruinderink, Leon and Pessl, Peter},
    journal = {{IACR Transactions on Cryptographic Hardware and Embedded Systems}},
       issn = {2569-2925},
        doi = {10.46586/tches.v2018.i3.21-43},
  publisher = {{Universitatsbibliothek der Ruhr-Universitat Bochum}},
       year = {2018},
      month = {8},
      pages = {21–43}
}""",
        "apa": """Groot Bruinderink, L., & Pessl, P. (2018). Differential Fault Attacks on Deterministic Lattice Signatures. IACR Transactions on Cryptographic Hardware and Embedded Systems, 21–43. https://doi.org/10.46586/tches.v2018.i3.21-43""",
        "ieee": """[1] L. Groot Bruinderink and P. Pessl, “Differential Fault Attacks on Deterministic Lattice Signatures,” IACR Transactions on Cryptographic Hardware and Embedded Systems, pp. 21–43, Aug. 2018, ISSN: 2569-2925. DOI: 10.46586/tches.v2018.i3.21-43.""",
        "gbt7714": """[1] GROOT BRUINDERINK L, PESSL P. Differential Fault Attacks on Deterministic Lattice Signatures[J/OL]. IACR Transactions on Cryptographic Hardware and Embedded Systems, 2018: 21-43. DOI: 10.46586/tches.v2018.i3.21-43.""",
        "chicago": """Groot Bruinderink, Leon, and Peter Pessl. “Differential Fault Attacks on Deterministic Lattice Signatures.” IACR Transactions on Cryptographic Hardware and Embedded Systems, August 2018, 21–43. ISSN: 2569-2925. https://doi.org/10.46586/tches.v2018.i3.21-43.""",
    },
]


def test_example_formats():
    """Test that all style formats match the expected output in EXAMPLES."""
    from pybtex.database import parse_string

    for example in EXAMPLES:
        # Parse the BibTeX entry
        bib_data = parse_string(example["entry"], bib_format="bibtex", encoding="utf-8")
        entry = list(bib_data.entries.values())[0]

        # Test APA style
        apa_style = APAStyle()
        apa_template = apa_style.get_article_template(entry)
        apa_result = str(apa_template.format_data({"entry": entry, "bib_data": bib_data, "style": apa_style})).strip()
        assert apa_result == example["apa"], f"APA mismatch:\n  Got:      {apa_result}\n  Expected: {example['apa']}"

        # Test IEEE style - add label [1] as pybtex would
        ieee_style = IEEEStyle()
        ieee_template = ieee_style.get_article_template(entry)
        ieee_result = str(ieee_template.format_data({"entry": entry, "bib_data": bib_data, "style": ieee_style})).strip()
        ieee_result_with_label = f"[1] {ieee_result}"
        assert (
            ieee_result_with_label == example["ieee"]
        ), f"IEEE mismatch:\n  Got:      {ieee_result_with_label}\n  Expected: {example['ieee']}"

        # Test GBT7714 style - add label [1] as pybtex would
        gbt_style = GBT7714Style()
        gbt_template = gbt_style.get_article_template(entry)
        gbt_result = str(gbt_template.format_data({"entry": entry, "bib_data": bib_data, "style": gbt_style})).strip()
        gbt_result_with_label = f"[1] {gbt_result}"
        assert (
            gbt_result_with_label == example["gbt7714"]
        ), f"GBT7714 mismatch:\n  Got:      {gbt_result_with_label}\n  Expected: {example['gbt7714']}"

        # Test Chicago style - no label needed
        chi_style = ChicagoStyle()
        chi_template = chi_style.get_article_template(entry)
        chi_result = str(chi_template.format_data({"entry": entry, "bib_data": bib_data, "style": chi_style})).strip()
        assert (
            chi_result == example["chicago"]
        ), f"Chicago mismatch:\n  Got:      {chi_result}\n  Expected: {example['chicago']}"


def _r(node, entry, style=None):
    context = {"entry": entry, "bib_data": None, "style": style}
    return str(node.format_data(context)).strip()


def test_styles_coverage():
    def ctx(entry):
        return {"entry": entry}

    class NoP:
        pass

    p1 = Person(first="A", last="B")
    e_full = Entry(
        "a",
        fields={
            "title": "T",
            "journal": "J",
            "year": "2021",
            "doi": "10.1",
            "publisher": "P",
            "booktitle": "BT",
            "school": "S",
            "institution": "I",
            "volume": "1",
            "number": "2",
            "pages": "10",
            "address": "A",
        },
        persons={"author": [p1, p1, p1, p1, p1]},
    )

    # 1. GBT7714
    style_gbt = GBT7714Style()
    gn = GBTNames("author", str)
    assert gn.format_data(ctx(Entry("a"))) == ""
    assert gn.format_data({"entry": Entry("a")}) == ""
    assert gn.format_data(NoP()) == ""
    assert style_gbt.format_names("author", as_sentence=False).format_data(ctx(e_full))
    assert "T" in _r(style_gbt.get_inproceedings_template(e_full), e_full, style_gbt)
    for m in [
        style_gbt.get_article_template,
        style_gbt.get_book_template,
        style_gbt.get_phdthesis_template,
        style_gbt.get_techreport_template,
    ]:
        assert m(e_full)

    # 2. IEEE
    style_ieee = IEEEStyle()
    in_names = IEEENames("author", str)
    assert in_names.format_data(Entry("a")) == ""
    assert in_names.format_data(NoP()) == ""
    e2 = Entry("a", persons={"author": [p1, p1]})
    assert "and" in in_names.format_data(ctx(e2))
    assert "p. 5" in _r(ieee_pages, Entry("a", fields={"pages": "5"}))
    assert "DOI" in _r(style_ieee.get_phdthesis_template(e_full), e_full, style_ieee)
    assert style_ieee.format_names("author", as_sentence=False).format_data(ctx(e_full))
    for m in [style_ieee.get_article_template, style_ieee.get_book_template, style_ieee.get_inproceedings_template]:
        assert m(e_full)

    # 3. APA
    style_apa = APAStyle()
    an = APANames("author", str)
    assert an.format_data(Entry("a")) == ""
    assert an.format_data(NoP()) == ""
    apa_style_names_check = str(
        an.format_data(ctx(Entry("a", persons={"author": [Person(str(i)) for i in range(21)]})))
    )  # 21+ authors
    assert "..." in apa_style_names_check
    assert style_apa.format_names("author", as_sentence=False).format_data(ctx(e_full))
    assert "L, Jr." in style_apa._format_person(Person(last="L", lineage="Jr."))
    assert "https" not in _r(
        style_apa.get_article_template(Entry("a", fields={"title": "T", "year": "2021", "journal": "J"})),
        Entry("a", fields={"title": "T", "year": "2021", "journal": "J"}),
        style_apa,
    )
    assert "T" in _r(
        style_apa.get_book_template(Entry("b", fields={"title": "T", "year": "2021", "publisher": "P"})),
        Entry("b", fields={"title": "T", "year": "2021", "publisher": "P"}),
        style_apa,
    )
    assert "BT" in _r(style_apa.get_inproceedings_template(e_full), e_full, style_apa)

    # 4. Chicago
    style_chi = ChicagoStyle()
    cn = ChicagoNames("author", lambda p, first_author=False: "N")
    assert cn.format_data(Entry("a")) == ""
    assert cn.format_data(NoP()) == ""
    assert "and" in str(cn.format_data(ctx(e2)))
    cn_long = ChicagoNames("author", lambda p, first_author=False: "N")
    e11 = Entry("a", persons={"author": [Person(str(i)) for i in range(11)]})
    assert "et al" in cn_long.format_data(ctx(e11))
    assert style_chi.format_names("author", as_sentence=False).format_data(ctx(e_full))
    assert isinstance(style_chi.format_names("author", as_sentence=True), Node)
    assert style_chi.format_label(e2) == ""
    assert "" == _r(chicago_date, Entry("a"))
    assert "https" not in _r(
        style_chi.get_article_template(Entry("a", fields={"title": "T", "journal": "J", "year": "2021"})),
        Entry("a", fields={"title": "T", "journal": "J", "year": "2021"}),
        style_chi,
    )


def test_additional_coverage():
    """Additional tests to improve coverage."""

    def ctx(entry):
        return {"entry": entry}

    p1 = Person(first="A", last="B")

    # Test APA with empty persons list
    style_apa = APAStyle()
    empty_entry = Entry("a", persons={"author": []})
    an = APANames("author", str)
    assert an.format_data(ctx(empty_entry)) == ""

    # Test APA format_names with as_sentence=True
    entry_with_author = Entry("a", persons={"author": [p1]})
    result = style_apa.format_names("author", as_sentence=True).format_data(ctx(entry_with_author))
    assert result is not None

    # Test APA inproceedings template without DOI
    inproc_no_doi = Entry("c", fields={"title": "T", "year": "2021", "booktitle": "BT"})
    inproc_no_doi.persons["author"] = [p1]
    apa_inproc_result = str(style_apa.get_inproceedings_template(inproc_no_doi).format_data(ctx(inproc_no_doi))).strip()
    assert "BT" in apa_inproc_result

    # Test APA with URL (book template with doi)
    book_with_doi = Entry("b", fields={"title": "T", "year": "2021", "publisher": "P", "doi": "10.1"})
    apa_book_result = str(style_apa.get_book_template(book_with_doi).format_data(ctx(book_with_doi))).strip()
    assert "https://doi.org/10.1" in apa_book_result

    # Test APA with its `format_label` method
    assert style_apa.format_label(Entry("a")) == ""  # APA doesn't use labels, should return empty string

    # Test IEEE with empty persons list
    style_ieee = IEEEStyle()
    ieee_empty = Entry("a", persons={"author": []})
    in_names = IEEENames("author", str)
    assert in_names.format_data(ctx(ieee_empty)) == ""

    # Test IEEE pages with no pages field
    entry_no_pages = Entry("a")
    assert "" == _r(ieee_pages, entry_no_pages)

    entry_empty_pages = Entry("a", fields={"pages": ""})
    assert "" == _r(ieee_pages, entry_empty_pages)

    # Test IEEE pages with single page
    entry_single_page = Entry("a", fields={"pages": "5"})
    assert "p. 5" in _r(ieee_pages, entry_single_page)

    # Test IEEE book template with DOI
    ieee_book_doi = Entry("b", fields={"title": "T", "publisher": "P", "year": "2021", "doi": "10.1"})
    ieee_book_doi.persons["author"] = [p1]
    ieee_book_doi_result = str(style_ieee.get_book_template(ieee_book_doi).format_data(ctx(ieee_book_doi))).strip()
    assert "DOI" in ieee_book_doi_result

    # Test IEEE inproceedings template without DOI
    ieee_inproc_no_doi = Entry("c", fields={"title": "T", "booktitle": "BT", "year": "2021", "pages": "10-20"})
    ieee_inproc_no_doi.persons["author"] = [p1]
    ieee_inproc_no_doi_result = str(
        style_ieee.get_inproceedings_template(ieee_inproc_no_doi).format_data(ctx(ieee_inproc_no_doi))
    ).strip()
    assert "BT" in ieee_inproc_no_doi_result

    # Test IEEE format_names with as_sentence=True
    ieee_names_result = style_ieee.format_names("author", as_sentence=True).format_data(ctx(entry_with_author))
    assert ieee_names_result is not None

    # Test IEEE with URL but no DOI
    ieee_url_only = Entry("a", fields={"title": "T", "journal": "J", "year": "2021", "url": "http://example.com"})
    ieee_url_only.persons["author"] = [p1]
    ieee_url_result = str(style_ieee.get_article_template(ieee_url_only).format_data(ctx(ieee_url_only))).strip()
    assert "[Online]. Available:" in ieee_url_result

    # Test IEEE with both DOI and URL
    ieee_both = Entry("a", fields={"title": "T", "journal": "J", "year": "2021", "doi": "10.1", "url": "http://example.com"})
    ieee_both.persons["author"] = [p1]
    ieee_both_result = str(style_ieee.get_article_template(ieee_both).format_data(ctx(ieee_both))).strip()
    assert "DOI:" in ieee_both_result
    assert "URL:" in ieee_both_result

    # Test GBT7714 with empty persons
    style_gbt = GBT7714Style()
    gbt_empty = Entry("a", persons={"author": []})
    gn = GBTNames("author", str)
    assert gn.format_data(ctx(gbt_empty)) == ""

    # Test GBT7714 format_names with as_sentence=True
    gbt_names_sentence = style_gbt.format_names("author", as_sentence=True).format_data(ctx(entry_with_author))
    assert gbt_names_sentence is not None

    # Test GBT7714 _format_person with prelast and lineage
    person_with_prelast = Person(first="F", prelast="Pre", last="L")
    gbt_prelast_result = style_gbt._format_person(person_with_prelast)
    assert "PRE L" in gbt_prelast_result  # GBT uses uppercase

    person_with_lineage = Person(first="F", last="L", lineage="Jr.")
    gbt_lineage_result = style_gbt._format_person(person_with_lineage)
    assert "JR" in gbt_lineage_result  # GBT uses uppercase

    # Test GBT7714 book template without DOI
    gbt_book_no_doi = Entry("b", fields={"title": "T", "publisher": "P", "year": "2021", "address": "A"})
    gbt_book_no_doi.persons["author"] = [p1]
    gbt_book_no_doi_result = str(style_gbt.get_book_template(gbt_book_no_doi).format_data(ctx(gbt_book_no_doi))).strip()
    assert "[M]" in gbt_book_no_doi_result

    # Test GBT7714 inproceedings template without DOI
    gbt_inproc_no_doi = Entry(
        "c", fields={"title": "T", "booktitle": "BT", "year": "2021", "pages": "10-20", "address": "A", "publisher": "P"}
    )
    gbt_inproc_no_doi.persons["author"] = [p1]
    gbt_inproc_no_doi_result = str(
        style_gbt.get_inproceedings_template(gbt_inproc_no_doi).format_data(ctx(gbt_inproc_no_doi))
    ).strip()
    assert "[C]" in gbt_inproc_no_doi_result

    # Test GBT7714 phdthesis template without DOI
    gbt_phd_no_doi = Entry("d", fields={"title": "T", "school": "S", "year": "2021", "address": "A"})
    gbt_phd_no_doi.persons["author"] = [p1]
    gbt_phd_no_doi_result = str(style_gbt.get_phdthesis_template(gbt_phd_no_doi).format_data(ctx(gbt_phd_no_doi))).strip()
    assert "[D]" in gbt_phd_no_doi_result

    # Test GBT7714 mastersthesis template
    gbt_masters = Entry("d", fields={"title": "T", "school": "S", "year": "2021"})
    gbt_masters.persons["author"] = [p1]
    gbt_masters_result = str(style_gbt.get_mastersthesis_template(gbt_masters).format_data(ctx(gbt_masters))).strip()
    assert "[D]" in gbt_masters_result

    # Test GBT7714 techreport template
    gbt_tech = Entry("r", fields={"title": "T", "institution": "I", "year": "2021", "doi": "10.1"})
    gbt_tech.persons["author"] = [p1]
    gbt_tech_result = str(style_gbt.get_techreport_template(gbt_tech).format_data(ctx(gbt_tech))).strip()
    assert "[R]" in gbt_tech_result

    # Test Chicago with empty persons
    style_chi = ChicagoStyle()
    chi_empty = Entry("a", persons={"author": []})
    cn = ChicagoNames("author", lambda p, first_author=False: "N")
    assert cn.format_data(ctx(chi_empty)) == ""

    # Test Chicago date with only year
    entry_year_only = Entry("a", fields={"year": "2021"})
    chi_date_result = _r(chicago_date, entry_year_only)
    assert "(2021)" in chi_date_result

    # Test Chicago book template without DOI
    chi_book_no_doi = Entry("b", fields={"title": "T", "publisher": "P", "year": "2021", "address": "A"})
    chi_book_no_doi.persons["author"] = [p1]
    chi_book_no_doi_result = str(style_chi.get_book_template(chi_book_no_doi).format_data(ctx(chi_book_no_doi))).strip()
    assert "T" in chi_book_no_doi_result

    # Test Chicago book template with DOI
    chi_book_doi = Entry("b", fields={"title": "T", "publisher": "P", "year": "2021", "doi": "10.1"})
    chi_book_doi.persons["author"] = [p1]
    chi_book_doi_result = str(style_chi.get_book_template(chi_book_doi).format_data(ctx(chi_book_doi))).strip()
    assert "https://doi.org/10.1" in chi_book_doi_result

    # Test Chicago inproceedings template without DOI
    chi_inproc_no_doi = Entry(
        "c", fields={"title": "T", "booktitle": "BT", "year": "2021", "pages": "10-20", "address": "A", "publisher": "P"}
    )
    chi_inproc_no_doi.persons["author"] = [p1]
    chi_inproc_no_doi_result = str(
        style_chi.get_inproceedings_template(chi_inproc_no_doi).format_data(ctx(chi_inproc_no_doi))
    ).strip()
    assert "BT" in chi_inproc_no_doi_result

    # Test Chicago inproceedings template with DOI
    chi_inproc_doi = Entry(
        "c", fields={"title": "T", "booktitle": "BT", "year": "2021", "pages": "10-20", "publisher": "P", "doi": "10.1"}
    )
    chi_inproc_doi.persons["author"] = [p1]
    chi_inproc_doi_result = str(style_chi.get_inproceedings_template(chi_inproc_doi).format_data(ctx(chi_inproc_doi))).strip()
    assert "https://doi.org/10.1" in chi_inproc_doi_result

    # Test Chicago _format_person with lineage
    person_with_lineage = Person(first="First", last="Last", lineage="Jr.")
    chi_lineage_result = style_chi._format_person(person_with_lineage, first_author=True)
    assert "Jr." in chi_lineage_result

    # Test Chicago _format_person with first_author=False
    chi_not_first_result = style_chi._format_person(p1, first_author=False)
    assert "A B" in chi_not_first_result

    # Test chicago_pages with no pages
    entry_no_pages = Entry("a")
    assert "" == _r(chicago_pages, entry_no_pages)

    # Test ieee_month with no month
    entry_no_month = Entry("a")
    assert "" == _r(ieee_month, entry_no_month)

    # Test IEEE _format_person_full_first with lineage
    person_with_lineage_ieee = Person(first="First", last="Last", lineage="Jr.")
    ieee_lineage_result = style_ieee._format_person(person_with_lineage_ieee)
    assert "Jr." in ieee_lineage_result

    # Test IEEE _format_person without initials
    person_no_initials = Person(last="OnlyLast")
    ieee_no_initials_result = style_ieee._format_person(person_no_initials)
    assert "OnlyLast" == ieee_no_initials_result

    # Test IEEE compact format without DOI
    ieee_compact_no_doi = Entry("a", fields={"title": "T", "journal": "J", "year": "2021", "volume": "1"})
    ieee_compact_no_doi.persons["author"] = [Person(str(i)) for i in range(10)]  # More than max_names (6)
    ieee_compact_no_doi_result = str(
        style_ieee.get_article_template(ieee_compact_no_doi).format_data(ctx(ieee_compact_no_doi))
    ).strip()
    assert "et al." in ieee_compact_no_doi_result

    # Test IEEE standard format without DOI or URL
    ieee_standard_nothing = Entry("a", fields={"title": "T", "journal": "J", "year": "2021"})
    ieee_standard_nothing.persons["author"] = [p1]
    ieee_standard_nothing_result = str(
        style_ieee.get_article_template(ieee_standard_nothing).format_data(ctx(ieee_standard_nothing))
    ).strip()
    assert "T" in ieee_standard_nothing_result

    # Test IEEE mastersthesis template
    ieee_masters = Entry("d", fields={"title": "T", "school": "S", "year": "2021", "doi": "10.1"})
    ieee_masters.persons["author"] = [p1]
    ieee_masters_result = str(style_ieee.get_mastersthesis_template(ieee_masters).format_data(ctx(ieee_masters))).strip()
    assert "M.S. thesis" in ieee_masters_result
    assert "DOI" in ieee_masters_result

    # Test IEEE _format_person_full_first with lineage
    person_lineage_full = Person(first="First", last="Last", lineage="III")
    ieee_names_class = IEEENames("author", style_ieee._format_person)
    ieee_full_lineage = ieee_names_class._format_person_full_first(person_lineage_full)
    assert "III" in ieee_full_lineage

    # Test IEEE format_label
    assert style_ieee.format_label(Entry("a")) == ""

    # Test chicago_date_plain with month + year
    entry_month_year = Entry("a", fields={"month": "8", "year": "2018"})
    assert _r(chicago_date_plain, entry_month_year) == "August 2018"

    # Test chicago_date_plain with year only
    entry_year_only2 = Entry("a", fields={"year": "2021"})
    assert _r(chicago_date_plain, entry_year_only2) == "2021"

    # Test chicago_date_plain with no fields
    assert _r(chicago_date_plain, Entry("a")) == ""

    # Test gbt_year_vol_pages: no volume, with pages (uses colon separator, hyphen in range)
    entry_no_vol = Entry("a", fields={"year": "2018", "pages": "21\u201343"})
    assert _r(gbt_year_vol_pages, entry_no_vol) == "2018: 21-43"

    # Test gbt_year_vol_pages: with volume and number
    entry_vol_num = Entry("a", fields={"year": "2022", "volume": "43", "number": "11", "pages": "115006"})
    assert _r(gbt_year_vol_pages, entry_vol_num) == "2022, 43(11): 115006"

    # Test gbt_year_vol_pages: with volume only (no number, no pages)
    entry_vol_only = Entry("a", fields={"year": "2021", "volume": "120"})
    assert _r(gbt_year_vol_pages, entry_vol_only) == "2021, 120"

    # Test gbt_year_vol_pages: year only (no volume, no pages)
    entry_year_only3 = Entry("a", fields={"year": "2021"})
    assert _r(gbt_year_vol_pages, entry_year_only3) == "2021"


def test_misc():
    with pytest.raises(ValueError):
        GBTNames("author", str, limit=0)
    from bib_lookup import BibLookup

    assert BibLookup(verbose=0).max_names == 3
    for node in [ieee_pages, ieee_month, chicago_pages, chicago_date]:
        assert str(node.format_data({})) == ""


def test_text_format_unquoted_full_month_name(monkeypatch):
    """``--format text --style gbt`` (and other pybtex-backed styles) must not
    return ``Not Found`` when the raw BibTeX contains an unquoted full month
    name like ``month=June`` — pybtex treats bare words as macros and raises
    ``UndefinedMacro`` unless the raw BibTeX is normalised beforehand."""

    from bib_lookup import BibLookup

    # Raw BibTeX as returned by some DOI resolvers (e.g. Springer via crossref)
    RAW_WITH_UNQUOTED_MONTH = """@article{An_2018, title={Prediction of remaining useful life under different conditions using accelerated life testing data}, volume={32}, ISSN={1976-3824}, url={http://dx.doi.org/10.1007/s12206-018-0507-z}, DOI={10.1007/s12206-018-0507-z}, number={6}, journal={Journal of Mechanical Science and Technology}, publisher={Springer Science and Business Media LLC}, author={An, Dawn and Choi, Joo-Ho and Kim, Nam Ho}, year={2018}, month=June, pages={2497–2507} }"""

    def _fake_obtain_feed_content(self, identifier, arxiv2doi=None, format=None, style=None, timeout=None):
        return ("doi", {}, "10.1007/s12206-018-0507-z")

    def _fake_handle_doi(self, feed_content):
        return RAW_WITH_UNQUOTED_MONTH

    monkeypatch.setattr(BibLookup, "_obtain_feed_content", _fake_obtain_feed_content)
    monkeypatch.setattr(BibLookup, "_handle_doi", _fake_handle_doi)

    bl = BibLookup(verbose=0)

    # 1. GBT7714 style (uppercases author names per the standard)
    result = bl("10.1007/s12206-018-0507-z", format="text", style="gbt", print_result=False)
    assert result not in (None, "Not Found"), f"GBT7714 failed: {result!r}"
    assert "Prediction" in result
    assert "AN" in result  # GBT7714 uppercases surnames

    # 2. IEEE style — same unquoted month should not break it
    result_ieee = bl("10.1007/s12206-018-0507-z", format="text", style="ieee", print_result=False)
    assert result_ieee not in (None, "Not Found"), f"IEEE failed: {result_ieee!r}"
    assert "An" in result_ieee

    # 3. APA style
    result_apa = bl("10.1007/s12206-018-0507-z", format="text", style="apa", print_result=False)
    assert result_apa not in (None, "Not Found"), f"APA failed: {result_apa!r}"
    assert "An" in result_apa

    # 4. Chicago style
    result_chi = bl("10.1007/s12206-018-0507-z", format="text", style="chicago", print_result=False)
    assert result_chi not in (None, "Not Found"), f"Chicago failed: {result_chi!r}"
    assert "An" in result_chi


def test_text_format_missing_journal(monkeypatch):
    """``--format text --style ...`` must not crash (or silently return
    an error) when the ``@article`` entry has no ``journal`` field —
    e.g. preprints from bioRxiv / medRxiv."""

    from bib_lookup import BibLookup

    # @article without journal (typical for preprint servers)
    RAW_NO_JOURNAL = """@article{Chan_2025, title={ENTAgents: AI Agents for Complex Knowledge Otolaryngology}, url={http://dx.doi.org/10.1101/2025.01.01.25319863}, DOI={10.1101/2025.01.01.25319863}, publisher={openRxiv}, author={Chan, Tsz Kin and Dinh, Ngoc-Duy}, year={2025}, month={1} }"""

    def _fake_obtain_feed_content(self, identifier, arxiv2doi=None, format=None, style=None, timeout=None):
        return ("doi", {}, "10.1101/2025.01.01.25319863")

    def _fake_handle_doi(self, feed_content):
        return RAW_NO_JOURNAL

    monkeypatch.setattr(BibLookup, "_obtain_feed_content", _fake_obtain_feed_content)
    monkeypatch.setattr(BibLookup, "_handle_doi", _fake_handle_doi)

    bl = BibLookup(verbose=0)

    for style in ["gbt", "ieee", "apa", "chicago"]:
        result = bl("10.1101/2025.01.01.25319863", format="text", style=style, print_result=False)
        assert result is not None, f"{style}: result is None"
        assert result not in bl.lookup_errors, f"{style}: got lookup error {result!r}"
        assert not result.startswith("Format Error"), f"{style}: format error: {result!r}"
        assert (
            "ENTAgents" in result or "Entagents" in result or "Chan" in result
        ), f"{style}: output doesn't contain expected text: {result!r}"
